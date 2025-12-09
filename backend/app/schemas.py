"""Pydantic schemas for request/response validation."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RuleFired(BaseModel):
    """Schema for a fired rule explanation."""
    rule_id: str
    rule_label: str
    points: float
    reason: str


class CustomerScore(BaseModel):
    """Schema for a customer with scoring information."""
    customer_id: Optional[str] = None
    priority_score: float
    priority_label: str  # "high", "medium", "low"
    rules_fired: List[RuleFired]
    explain: Dict[str, Any] = Field(default_factory=dict)
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class ScoreRequest(BaseModel):
    """Request schema for scoring endpoint."""
    data: List[Dict[str, Any]] = Field(..., description="List of customer records to score")


class ScoreResponse(BaseModel):
    """Response schema for scoring endpoint."""
    results: List[CustomerScore]
    total_scored: int
    summary: Dict[str, int] = Field(default_factory=dict)
    model_scores: Optional[Dict[str, List[float]]] = None


class RecommendationResponse(BaseModel):
    """Response schema for recommendations endpoint."""
    customers: List[CustomerScore]
    total_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerDetailResponse(BaseModel):
    """Response schema for customer detail endpoint."""
    customer: CustomerScore
    suggested_action: str


class RuleConfig(BaseModel):
    """Schema for a rule configuration."""
    id: str
    label: str
    condition: str
    points: float
    description: str
    enabled: bool = True
    threshold: Optional[float] = None


class RulesResponse(BaseModel):
    """Response schema for rules endpoint."""
    rules: List[RuleConfig]


class RuleUpdateRequest(BaseModel):
    """Request schema for updating a rule."""
    enabled: Optional[bool] = None
    threshold: Optional[float] = None
    points: Optional[float] = None


class CampaignSimulationRequest(BaseModel):
    """Request schema for campaign simulation."""
    top_n: int = Field(default=50, ge=1, le=10000)
    filter_criteria: Optional[Dict[str, Any]] = None


class CampaignSimulationResponse(BaseModel):
    """Response schema for campaign simulation."""
    estimated_conversion_rate: float
    estimated_revenue: float
    total_customers: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    kpis: Dict[str, Any] = Field(default_factory=dict)


class DatasetMetadataResponse(BaseModel):
    """Metadata about an ingested dataset."""
    dataset_id: str
    source_filename: str
    ingestion_timestamp: str
    records_total: int
    records_valid: int
    records_invalid: int
    columns: List[str]


class ModelTrainingResponse(BaseModel):
    """Response containing training metrics and versions."""
    dataset_id: str
    models: Dict[str, Any]


class ModelTrainingRequest(BaseModel):
    """Request controlling model training execution."""
    dataset_id: Optional[str] = None
    model_names: Optional[List[str]] = None


class ModelPredictionRequest(BaseModel):
    """Request for model inference using the latest registered model."""
    model_name: str
    records: List[Dict[str, Any]]


class ModelPredictionResponse(BaseModel):
    """Response containing model predictions and explanations."""
    model_name: str
    version: str
    probabilities: List[float]
    predictions: List[int]
    explanations: Optional[List[Dict[str, Any]]] = None


class MonitoringMetricsResponse(BaseModel):
    """Response for monitoring metrics and drift detection."""
    metrics: Dict[str, Any]
    drift: Dict[str, Any]


class ColumnStatisticsResponse(BaseModel):
    """Response containing column statistics for visualizations."""
    columns: List[str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    column_stats: Dict[str, Any]
    available_charts: List[str] = Field(
        default_factory=lambda: ["bar", "pie", "line", "area", "scatter", "histogram", "box"]
    )


class AIAnalysisResponse(BaseModel):
    """Response containing AI agent analysis and recommendations."""
    analysis: Dict[str, Any]
    recommendations: Dict[str, Any]
    transformation_plan: Dict[str, Any]
    suggested_charts: List[Dict[str, Any]]
    feature_engineering_suggestions: List[Dict[str, Any]]
    ai_enabled: bool = True


