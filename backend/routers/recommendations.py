"""Recommendations endpoint."""
from fastapi import APIRouter

from models.schemas import FileIdRequest, RecommendationResponse
from services.agent import SmartRecoAgent
from utils import helpers

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Generate recommendations and actions",
)
async def recommendations(request: FileIdRequest) -> RecommendationResponse:
    """Generate business recommendations based on heuristic analysis."""
    df = helpers.load_dataframe(request.file_id)
    agent = SmartRecoAgent(df, request.file_id)
    return agent.recommend()


