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
    ModelPredictionRequest, ModelPredictionResponse, MonitoringMetricsResponse,
    ColumnStatisticsResponse, AIAnalysisResponse,
    DashboardFragmentResponse, DashboardWidget
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
from .schema_detection import schema_detector
from .ai_agent import ai_agent

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
        "dataset_loaded": latest_dataset_id is not None,
        "scored_count": len(scored_customers_cache)
    }


@app.post("/upload", response_model=DatasetMetadataResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV dataset. Supports any CSV structure and large files (chunked processing).
    
    Returns:
        Upload confirmation with row count and error report if applicable.
    """
    global scored_customers_cache, latest_dataset_metadata, latest_dataset_id, reference_score_series, explainability_service

    try:
        # Check file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 500:  # 500MB limit
            raise HTTPException(
                status_code=400, 
                detail=f"File too large: {file_size_mb:.2f}MB. Maximum size is 500MB."
            )
        
        # Try different encodings
        csv_content = None
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                csv_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if csv_content is None:
            raise HTTPException(status_code=400, detail="Could not decode file. Please ensure it's a valid CSV file.")

        # Parse CSV with chunking support for large files
        if file_size_mb > 10:  # Use chunking for files > 10MB
            logger.info(f"Large file detected ({file_size_mb:.2f}MB), using chunked processing")
            # For very large files, we'll process in chunks
            from io import StringIO
            import pandas as pd
            chunk_list = []
            chunk_size = 50000
            for chunk in pd.read_csv(StringIO(csv_content), chunksize=chunk_size, low_memory=False):
                chunk_list.append(chunk)
            df = pd.concat(chunk_list, ignore_index=True)
            logger.info(f"Loaded {len(df)} rows from {len(chunk_list)} chunks")
        else:
            df = parse_csv_data(csv_content)

        # Ingest and persist dataset (with automatic chunking for large datasets)
        metadata = data_ingestion_service.ingest(
            df, 
            source_filename=file.filename,
            use_chunks=file_size_mb > 10
        )
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
    except HTTPException:
        raise
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


@app.get("/datasets/latest/statistics", response_model=ColumnStatisticsResponse)
async def get_dataset_statistics():
    """Get column statistics for the latest dataset (for visualizations)."""
    if latest_dataset_id is None:
        raise HTTPException(status_code=404, detail="No dataset has been uploaded yet.")
    
    try:
        dataset = storage_manager.load_dataframe(
            latest_dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
        )
        
        # Detect schema
        schema = schema_detector.detect_schema(dataset, sample_size=min(10000, len(dataset)))
        
        return ColumnStatisticsResponse(
            columns=schema["columns"],
            numeric_columns=schema["numeric_columns"],
            categorical_columns=schema["categorical_columns"],
            datetime_columns=schema["datetime_columns"],
            column_stats=schema["column_stats"],
        )
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {str(exc)}")


@app.get("/datasets/latest/ai-analysis", response_model=AIAnalysisResponse)
async def get_ai_analysis():
    """
    Get AI agent analysis and recommendations for the latest dataset.
    Uses Gemini AI to analyze the data and suggest transformations and visualizations.
    """
    if latest_dataset_id is None:
        raise HTTPException(status_code=404, detail="No dataset has been uploaded yet.")
    
    try:
        dataset = storage_manager.load_dataframe(
            latest_dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
        )
        
        # Check if AI analysis already exists in metadata
        if latest_dataset_metadata and latest_dataset_metadata.get("ai_analysis"):
            ai_analysis = latest_dataset_metadata["ai_analysis"]
            return AIAnalysisResponse(
                analysis=ai_analysis.get("analysis", {}),
                recommendations=ai_analysis.get("recommendations", {}),
                transformation_plan=ai_analysis.get("transformation_plan", {}),
                suggested_charts=ai_analysis.get("suggested_charts", []),
                feature_engineering_suggestions=ai_analysis.get("feature_engineering_suggestions", []),
                ai_enabled=settings.AI_AGENT_ENABLED and ai_agent.model is not None,
            )
        
        # Run new analysis
        logger.info("Running AI agent analysis...")
        ai_analysis = ai_agent.analyze_dataset(dataset, sample_size=min(5000, len(dataset)))
        
        return AIAnalysisResponse(
            analysis=ai_analysis.get("analysis", {}),
            recommendations=ai_analysis.get("recommendations", {}),
            transformation_plan=ai_analysis.get("transformation_plan", {}),
            suggested_charts=ai_analysis.get("suggested_charts", []),
            feature_engineering_suggestions=ai_analysis.get("feature_engineering_suggestions", []),
            ai_enabled=settings.AI_AGENT_ENABLED and ai_agent.model is not None,
        )
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {str(exc)}")
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error running AI analysis: {str(e)}")


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


@app.post("/dashboard/generate-fragment", response_model=DashboardFragmentResponse)
async def generate_dashboard_fragment():
    """
    Generate a dashboard fragment using AI analysis of available data.
    
    Returns:
        DashboardFragmentResponse with AI-generated widgets
    """
    global scored_customers_cache, latest_dataset_id
    
    try:
        widgets = []
        
        # Si on a des clients scorés, générer des widgets basés sur eux
        if scored_customers_cache:
            # Widget KPI: Total clients scorés
            widgets.append(DashboardWidget(
                id="widget_kpi_total",
                type="kpi",
                title="Total Clients Scorés",
                data={
                    "value": len(scored_customers_cache),
                    "trend": "neutral"
                },
                config={"subtitle": "Clients analysés", "unit": "clients"}
            ))
            
            # Widget KPI: Score moyen
            avg_score = sum(c.priority_score for c in scored_customers_cache) / len(scored_customers_cache) if scored_customers_cache else 0
            widgets.append(DashboardWidget(
                id="widget_kpi_avg_score",
                type="kpi",
                title="Score Moyen",
                data={
                    "value": round(avg_score, 2),
                    "trend": "up" if avg_score > 30 else "neutral"
                },
                config={"subtitle": "Score de priorité moyen", "unit": "points"}
            ))
            
            # Widget Bar: Distribution par priorité
            priority_counts = {}
            for customer in scored_customers_cache:
                label = customer.priority_label
                priority_counts[label] = priority_counts.get(label, 0) + 1
            
            widgets.append(DashboardWidget(
                id="widget_bar_priority",
                type="bar",
                title="Distribution par Priorité",
                data=[
                    {"name": "Haute", "value": priority_counts.get("high", 0)},
                    {"name": "Moyenne", "value": priority_counts.get("medium", 0)},
                    {"name": "Basse", "value": priority_counts.get("low", 0)}
                ]
            ))
            
            # Widget Pie: Répartition des règles déclenchées
            rule_counts = {}
            for customer in scored_customers_cache[:100]:  # Limiter pour performance
                for rule in customer.rules_fired:
                    rule_counts[rule.rule_label] = rule_counts.get(rule.rule_label, 0) + 1
            
            top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            widgets.append(DashboardWidget(
                id="widget_pie_rules",
                type="pie",
                title="Top 5 Règles Déclenchées",
                data=[{"name": name, "value": count} for name, count in top_rules]
            ))
            
            # Widget Line: Distribution des scores
            score_ranges = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
            for customer in scored_customers_cache:
                score = customer.priority_score
                if score <= 25:
                    score_ranges["0-25"] += 1
                elif score <= 50:
                    score_ranges["26-50"] += 1
                elif score <= 75:
                    score_ranges["51-75"] += 1
                else:
                    score_ranges["76-100"] += 1
            
            widgets.append(DashboardWidget(
                id="widget_line_scores",
                type="line",
                title="Distribution des Scores",
                data=[
                    {"name": "0-25", "value": score_ranges["0-25"]},
                    {"name": "26-50", "value": score_ranges["26-50"]},
                    {"name": "51-75", "value": score_ranges["51-75"]},
                    {"name": "76-100", "value": score_ranges["76-100"]}
                ]
            ))
        
        # Si on a un dataset mais pas de clients scorés, générer des widgets basés sur le dataset
        elif latest_dataset_id:
            try:
                # Essayer de charger le dataset via storage_manager si disponible
                try:
                    dataset = storage_manager.load_dataframe(
                        latest_dataset_id,
                        subdir=getattr(settings, 'NORMALIZED_DATA_SUBDIR', 'normalized'),
                    )
                except (AttributeError, NameError):
                    # Si storage_manager n'est pas disponible, utiliser les métadonnées
                    if latest_dataset_metadata:
                        widgets.append(DashboardWidget(
                            id="widget_kpi_rows",
                            type="kpi",
                            title="Nombre de Lignes",
                            data={
                                "value": latest_dataset_metadata.get("records_total", 0),
                                "trend": "neutral"
                            },
                            config={"subtitle": "Lignes dans le dataset", "unit": "lignes"}
                        ))
                        widgets.append(DashboardWidget(
                            id="widget_kpi_cols",
                            type="kpi",
                            title="Nombre de Colonnes",
                            data={
                                "value": len(latest_dataset_metadata.get("columns", [])),
                                "trend": "neutral"
                            },
                            config={"subtitle": "Colonnes dans le dataset", "unit": "colonnes"}
                        ))
                    raise StopIteration  # Sortir de la boucle try
                
                # Widget KPI: Nombre de lignes
                widgets.append(DashboardWidget(
                    id="widget_kpi_rows",
                    type="kpi",
                    title="Nombre de Lignes",
                    data={
                        "value": len(dataset),
                        "trend": "neutral"
                    },
                    config={"subtitle": "Lignes dans le dataset", "unit": "lignes"}
                ))
                
                # Widget KPI: Nombre de colonnes
                widgets.append(DashboardWidget(
                    id="widget_kpi_cols",
                    type="kpi",
                    title="Nombre de Colonnes",
                    data={
                        "value": len(dataset.columns),
                        "trend": "neutral"
                    },
                    config={"subtitle": "Colonnes dans le dataset", "unit": "colonnes"}
                ))
                
                # Widget Table: Aperçu des données
                sample_data = dataset.head(10).to_dict('records')
                widgets.append(DashboardWidget(
                    id="widget_table_preview",
                    type="table",
                    title="Aperçu des Données",
                    data=sample_data,
                    config={"columns": list(dataset.columns[:5])}  # Limiter à 5 colonnes
                ))
                
            except StopIteration:
                pass  # Déjà géré avec les métadonnées
            except Exception as e:
                logger.error(f"Error loading dataset for dashboard: {e}")
        
        # Si aucun widget n'a été généré
        if not widgets:
            # Widget par défaut
            widgets.append(DashboardWidget(
                id="widget_default",
                type="kpi",
                title="Aucune Donnée",
                data={
                    "value": 0,
                    "trend": "neutral"
                },
                config={"subtitle": "Veuillez uploader un dataset", "unit": ""}
            ))
        
        return DashboardFragmentResponse(
            widgets=widgets,
            layout="grid",
            description=f"Fragment de dashboard généré avec {len(widgets)} widgets basés sur les données disponibles"
        )
        
    except Exception as e:
        logger.error(f"Error generating dashboard fragment: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating dashboard fragment: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


