"""FastAPI main application."""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from loguru import logger
import pandas as pd

from .config import settings
from .schemas import (
    ScoreRequest, ScoreResponse, RecommendationResponse,
    CustomerDetailResponse, RulesResponse, RuleUpdateRequest,
    CampaignSimulationRequest, CampaignSimulationResponse
)
from .scoring_rules import rule_engine
from .recommender import recommender
from .utils import parse_csv_data, generate_customer_id

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

# In-memory storage for uploaded dataset (for demo purposes)
uploaded_dataset: Optional[pd.DataFrame] = None
scored_customers_cache: List = []


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
        "dataset_loaded": uploaded_dataset is not None,
        "scored_count": len(scored_customers_cache)
    }


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV dataset.
    
    Returns:
        Upload confirmation with row count
    """
    global uploaded_dataset, scored_customers_cache
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        df = parse_csv_data(csv_content)
        
        # Store in memory
        uploaded_dataset = df
        scored_customers_cache = []
        
        logger.info(f"Uploaded dataset with {len(df)} rows and {len(df.columns)} columns")
        
        return {
            "status": "success",
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "message": "Dataset uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


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
            summary=summary
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
    global uploaded_dataset
    
    if uploaded_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded. Please upload a dataset first.")
    
    try:
        # Convert DataFrame to list of dictionaries
        customers_data = uploaded_dataset.to_dict('records')
        
        # Create score request
        request = ScoreRequest(data=customers_data)
        
        # Score using the main endpoint logic
        return await score_customers(request)
        
    except Exception as e:
        logger.error(f"Error scoring uploaded dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error scoring dataset: {str(e)}")


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


