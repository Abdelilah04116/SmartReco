"""Business rule extraction endpoint."""
from fastapi import APIRouter

from models.schemas import FileIdRequest, RuleResponse, RuleConfigRequest
from services.agent import SmartRecoAgent
from utils import helpers, cache

router = APIRouter(tags=["rules"])


@router.post("/rules", response_model=RuleResponse, summary="Extract business rules")
async def extract_rules(request: FileIdRequest) -> RuleResponse:
    """Generate rule candidates using deterministic heuristics."""
    cached = cache.get_cache(request.file_id)
    if cached and "rules" in cached:
        return RuleResponse(**cached["rules"])
    df = helpers.load_dataframe(request.file_id)
    agent = SmartRecoAgent(df, request.file_id)
    return agent.extract_rules()


@router.post("/rules/config", summary="Update rule thresholds/weights", response_model=dict)
async def configure_rules(request: RuleConfigRequest) -> dict:
    """
    Accepts user-provided weights/thresholds/multipliers and echoes back for now.
    A real implementation would persist and apply them inside the agent.
    """
    # Placeholder for persistence; here we simply return the provided config.
    return {
        "file_id": request.file_id,
        "weights": request.weights,
        "thresholds": request.thresholds,
        "multipliers": request.multipliers,
    }

