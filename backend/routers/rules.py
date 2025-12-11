"""Business rule extraction endpoint."""
from fastapi import APIRouter

from models.schemas import FileIdRequest, RuleResponse
from services.agent import SmartRecoAgent
from utils import helpers

router = APIRouter(tags=["rules"])


@router.post("/rules", response_model=RuleResponse, summary="Extract business rules")
async def extract_rules(request: FileIdRequest) -> RuleResponse:
    """Generate rule candidates using deterministic heuristics."""
    df = helpers.load_dataframe(request.file_id)
    agent = SmartRecoAgent(df, request.file_id)
    return agent.extract_rules()

