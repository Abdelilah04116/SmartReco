"""FastAPI main application."""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from loguru import logger
import pandas as pd

from .config import settings
from .schemas import (
    ScoreRequest, ScoreResponse, RecommendationResponse,
    CustomerDetailResponse, RulesResponse, RuleUpdateRequest,
    CampaignSimulationRequest, CampaignSimulationResponse,
    DatasetMetadataResponse, ModelTrainingRequest, ModelTrainingResponse,
    ModelPredictionRequest, ModelPredictionResponse, MonitoringMetricsResponse
)
from .scoring_rules import rule_engine
from .recommender import recommender
from .utils import parse_csv_data, generate_customer_id
from .data_pipeline import data_ingestion_service
from .storage import storage_manager, StorageError
from .modeling import ModelRegistry, ModelTrainingService
from .experiments.runner import ExperimentRunner
from .monitoring import compute_monitoring_metrics, detect_drift
from .explainability import ExplainabilityService

# Configure logging
logger.add("logs/app.log", rotation="10 MB", retention="10 days", level="INFO")

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Runtime state
scored_customers_cache: List = []
latest_dataset_metadata: Optional[Dict[str, Any]] = None
latest_dataset_id: Optional[str] = None
reference_score_series: Optional[pd.Series] = None

model_registry = ModelRegistry()
training_service = ModelTrainingService(model_registry)
experiment_runner = ExperimentRunner()
explainability_service: Optional[ExplainabilityService] = None


def _compute_model_scores(records: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Compute model probabilities for provided records using latest models."""
    model_scores: Dict[str, List[float]] = {}
    if not records:
        return model_scores

    df = pd.DataFrame(records)
    for model_name in ["logistic_regression", "gradient_boosting"]:
        try:
            model, feature_engineer, metadata = model_registry.load_latest(model_name)
        except FileNotFoundError:
            continue
        try:
            features = feature_engineer.transform(df)
            probabilities = model.predict_proba(features)[:, 1].tolist()
            model_scores[model_name] = probabilities
        except Exception as exc:
            logger.error(f"Error producing predictions with model {model_name}: {exc}")
            continue
    return model_scores


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key for protected endpoints."""
    if not settings.API_KEY:
        return True  # No API key required if not configured
    if x_api_key == settings.API_KEY:
        return True
    raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "smart-reco-api",
        "version": settings.API_VERSION
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "rules_loaded": len(rule_engine.get_rules()),
        "dataset_available": latest_dataset_id is not None,
        "scored_count": len(scored_customers_cache)
    }


@app.post("/upload", response_model=DatasetMetadataResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV dataset.
    
    Returns:
        Upload confirmation with row count
    """
    global scored_customers_cache, latest_dataset_metadata, latest_dataset_id, reference_score_series, explainability_service
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        df = parse_csv_data(csv_content)

        # Ingest and persist dataset
        metadata = data_ingestion_service.ingest(df, source_filename=file.filename)
        latest_dataset_metadata = metadata
        latest_dataset_id = metadata["dataset_id"]
        scored_customers_cache = []
        reference_score_series = None
        explainability_service = None

        logger.info(
            "Dataset uploaded and normalized",
            dataset_id=latest_dataset_id,
            records=metadata["quality_report"]["records_valid"],
        )

        return DatasetMetadataResponse(
            dataset_id=metadata["dataset_id"],
            source_filename=metadata["source_filename"],
            ingestion_timestamp=metadata["ingestion_timestamp"],
            records_total=metadata["quality_report"]["records_total"],
            records_valid=metadata["quality_report"]["records_valid"],
            records_invalid=metadata["quality_report"]["records_invalid"],
            columns=metadata["columns"],
        )

    except StorageError as exc:
        logger.error(f"Storage error during dataset upload: {exc}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(exc)}")
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@app.get("/datasets/latest", response_model=DatasetMetadataResponse)
async def get_latest_dataset_metadata():
    """Return metadata for the most recently ingested dataset."""
    if not latest_dataset_metadata:
        raise HTTPException(status_code=404, detail="No dataset has been uploaded yet.")
    meta = latest_dataset_metadata
    return DatasetMetadataResponse(
        dataset_id=meta["dataset_id"],
        source_filename=meta["source_filename"],
        ingestion_timestamp=meta["ingestion_timestamp"],
        records_total=meta["quality_report"]["records_total"],
        records_valid=meta["quality_report"]["records_valid"],
        records_invalid=meta["quality_report"]["records_invalid"],
        columns=meta["columns"],
    )


@app.post("/score", response_model=ScoreResponse)
async def score_customers(request: ScoreRequest):
    """
    Score customers based on business rules.
    
    Args:
        request: ScoreRequest with list of customer records
        
    Returns:
        ScoreResponse with scored customers and summary
    """
    global scored_customers_cache
    
    try:
        # Score all customers
        scored = recommender.score_customers(request.data)
        
        # Update cache
        scored_customers_cache = scored

        model_scores = _compute_model_scores(request.data)
        
        # Calculate summary
        summary = {
            "high": sum(1 for c in scored if c.priority_label == "high"),
            "medium": sum(1 for c in scored if c.priority_label == "medium"),
            "low": sum(1 for c in scored if c.priority_label == "low"),
            "total": len(scored)
        }
        
        logger.info(f"Scored {len(scored)} customers: {summary}")
        
        return ScoreResponse(
            results=scored,
            total_scored=len(scored),
            summary=summary,
            model_scores=model_scores or None,
        )
        
    except Exception as e:
        logger.error(f"Error scoring customers: {e}")
        raise HTTPException(status_code=500, detail=f"Error scoring customers: {str(e)}")


@app.post("/score/upload")
async def score_uploaded_dataset():
    """
    Score the previously uploaded dataset.
    
    Returns:
        ScoreResponse with scored customers
    """
    if latest_dataset_id is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded. Please upload a dataset first.")
    
    try:
        dataset = storage_manager.load_dataframe(
            latest_dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
        )
        customers_data = dataset.to_dict('records')
        
        # Create score request
        request = ScoreRequest(data=customers_data)
        
        # Score using the main endpoint logic
        return await score_customers(request)
        
    except StorageError as exc:
        logger.error(f"Error accessing stored dataset: {exc}")
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {str(exc)}")
    except Exception as e:
        logger.error(f"Error scoring uploaded dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error scoring dataset: {str(e)}")


@app.post("/models/train", response_model=ModelTrainingResponse)
async def train_models(request: ModelTrainingRequest):
    """Trigger supervised model training on the selected dataset."""
    dataset_id = request.dataset_id or latest_dataset_id
    if dataset_id is None:
        raise HTTPException(status_code=400, detail="No dataset available for training.")

    try:
        dataset = storage_manager.load_dataframe(
            dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
        )
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=f"Dataset unavailable: {str(exc)}") from exc

    artifacts = training_service.train_supervised_models(dataset)
    try:
        experiment_runner.run_supervised_benchmark(dataset_id)
    except Exception as exc:
        logger.warning(f"Experiment runner failed for dataset {dataset_id}: {exc}")

    models_payload = {
        name: {
            "version": artifact.version,
            "metrics": artifact.metrics,
        }
        for name, artifact in artifacts.items()
    }

    return ModelTrainingResponse(dataset_id=dataset_id, models=models_payload)


@app.post("/models/predict", response_model=ModelPredictionResponse)
async def model_predict(request: ModelPredictionRequest):
    """Run inference using the latest version of the requested model."""
    try:
        model, feature_engineer, metadata = model_registry.load_latest(request.model_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No trained model found for {request.model_name}")

    df = pd.DataFrame(request.records)
    try:
        features = feature_engineer.transform(df)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Feature transformation failed: {str(exc)}") from exc

    probabilities = model.predict_proba(features)[:, 1]
    predictions = model.predict(features)

    explanations_payload: Optional[List[Dict[str, Any]]] = None
    if request.records:
        global explainability_service
        if explainability_service is None:
            explainability_service = ExplainabilityService(feature_engineer)
            if latest_dataset_id:
                try:
                    dataset = storage_manager.load_dataframe(
                        latest_dataset_id,
                        subdir=settings.NORMALIZED_DATA_SUBDIR,
                    )
                    explainability_service.prepare_background(dataset.drop(columns=[settings.TARGET_COLUMN]))
                except Exception as exc:  # pragma: no cover - optional path
                    logger.warning(f"Unable to prepare explainability background: {exc}")

        if explainability_service and explainability_service.background_data is not None:
            explanations_payload = []
            for record_dict, proba in zip(request.records, probabilities):
                try:
                    rule_score = recommender.score_customer(record_dict)
                    bundle = explainability_service.explain_instance(
                        model,
                        pd.Series(record_dict),
                        rule_explanations={
                            "priority_score": rule_score.priority_score,
                            "priority_label": rule_score.priority_label,
                            "rules": [rf.model_dump() for rf in rule_score.rules_fired],
                        },
                    )
                    explanations_payload.append(bundle.__dict__)
                except Exception as exc:
                    logger.warning(f"Failed to compute explanation: {exc}")

    return ModelPredictionResponse(
        model_name=request.model_name,
        version=metadata["version"],
        probabilities=probabilities.tolist(),
        predictions=predictions.tolist(),
        explanations=explanations_payload,
    )


@app.get("/monitoring/metrics", response_model=MonitoringMetricsResponse)
async def monitoring_metrics():
    """Compute monitoring KPIs and drift detection for the latest dataset."""
    global reference_score_series

    if latest_dataset_id is None:
        raise HTTPException(status_code=404, detail="No dataset available for monitoring.")

    try:
        dataset = storage_manager.load_dataframe(
            latest_dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
        )
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=f"Dataset unavailable: {str(exc)}") from exc

    scored = recommender.score_customers(dataset.to_dict("records"))
    scores_series = pd.Series([s.priority_score for s in scored])
    outcomes_series = dataset[settings.TARGET_COLUMN]

    metrics = compute_monitoring_metrics(scores_series, outcomes_series)
    if reference_score_series is None:
        reference_score_series = scores_series
        drift = {
            "ks_statistic": None,
            "p_value": None,
            "drift_detected": False,
            "threshold": settings.DRIFT_THRESHOLD,
        }
    else:
        drift = detect_drift(scores_series, reference_score_series)
        reference_score_series = scores_series

    return MonitoringMetricsResponse(metrics=metrics, drift=drift)


@app.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    top_n: int = 50,
    priority_label: Optional[str] = None,
    min_score: Optional[float] = None
):
    """
    Get top N customer recommendations.
    
    Args:
        top_n: Number of top customers to return
        priority_label: Optional filter by priority label
        min_score: Optional minimum score filter
        
    Returns:
        RecommendationResponse with sorted customers
    """
    global scored_customers_cache
    
    if not scored_customers_cache:
        raise HTTPException(status_code=400, detail="No scored customers available. Please score customers first.")
    
    try:
        # Build filter criteria
        filter_criteria = {}
        if priority_label:
            filter_criteria['priority_label'] = priority_label
        if min_score is not None:
            filter_criteria['min_score'] = min_score
        
        # Get recommendations
        recommendations = recommender.get_recommendations(
            scored_customers_cache,
            top_n=top_n,
            filter_criteria=filter_criteria if filter_criteria else None
        )
        
        # Calculate metadata
        metadata = {
            "high_count": sum(1 for c in recommendations if c.priority_label == "high"),
            "medium_count": sum(1 for c in recommendations if c.priority_label == "medium"),
            "low_count": sum(1 for c in recommendations if c.priority_label == "low"),
            "avg_score": sum(c.priority_score for c in recommendations) / len(recommendations) if recommendations else 0.0
        }
        
        logger.info(f"Returned {len(recommendations)} recommendations (top_n={top_n})")
        
        return RecommendationResponse(
            customers=recommendations,
            total_count=len(recommendations),
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@app.get("/customer/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer_detail(customer_id: str):
    """
    Get detailed information about a specific customer.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        CustomerDetailResponse with customer details and suggested action
    """
    global scored_customers_cache
    
    # Find customer
    customer = None
    for c in scored_customers_cache:
        if c.customer_id == customer_id:
            customer = c
            break
    
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    
    # Generate suggested action
    suggested_action = recommender.generate_suggested_action(customer)
    
    return CustomerDetailResponse(
        customer=customer,
        suggested_action=suggested_action
    )


@app.get("/rules", response_model=RulesResponse)
async def get_rules():
    """Get all business rules configuration."""
    rules = rule_engine.get_rules()
    return RulesResponse(rules=rules)


@app.put("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    request: RuleUpdateRequest,
    api_key_verified: bool = Depends(verify_api_key)
):
    """
    Update a business rule configuration.
    
    Args:
        rule_id: ID of the rule to update
        request: Update request with new values
        
    Returns:
        Updated rule configuration
    """
    success = rule_engine.update_rule(
        rule_id=rule_id,
        enabled=request.enabled,
        threshold=request.threshold,
        points=request.points
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    # Save rules to file
    rule_engine.save_rules()
    
    updated_rule = rule_engine.get_rule(rule_id)
    return {"status": "success", "rule": updated_rule.model_dump()}


@app.post("/simulate_campaign", response_model=CampaignSimulationResponse)
async def simulate_campaign(request: CampaignSimulationRequest):
    """
    Simulate a marketing campaign and estimate KPIs.
    
    Args:
        request: Campaign simulation request with top_n
        
    Returns:
        CampaignSimulationResponse with estimated KPIs
    """
    global scored_customers_cache
    
    if not scored_customers_cache:
        raise HTTPException(status_code=400, detail="No scored customers available. Please score customers first.")
    
    try:
        simulation_results = recommender.simulate_campaign(
            scored_customers_cache,
            top_n=request.top_n
        )
        
        return CampaignSimulationResponse(**simulation_results)
        
    except Exception as e:
        logger.error(f"Error simulating campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulating campaign: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


