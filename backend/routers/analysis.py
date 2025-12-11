"""Analysis, plotting, and feature engineering endpoints."""
from fastapi import APIRouter

from models.schemas import AnalyzeResponse, FeatureResponse, PlotRequest, PlotResponse
from services.agent import SmartRecoAgent
from utils import helpers

router = APIRouter(tags=["analysis"])


def _agent(file_id: str) -> SmartRecoAgent:
    df = helpers.load_dataframe(file_id)
    return SmartRecoAgent(df, file_id)


@router.post("/analyze", response_model=AnalyzeResponse, summary="Run automatic analysis")
async def analyze(request: PlotRequest) -> AnalyzeResponse:
    """Execute the SmartReco agent for structure detection and stats."""
    agent = _agent(request.file_id)
    return agent.analyze()


@router.post("/plots", response_model=PlotResponse, summary="Generate plots")
async def plots(request: PlotRequest) -> PlotResponse:
    """Generate matplotlib plots as base64 strings."""
    agent = _agent(request.file_id)
    analysis = agent.analyze()
    requested = (
        [p for p in analysis.suggested_plots if p["plot_type"] in request.plot_types]
        if request.plot_types
        else analysis.suggested_plots
    )
    return agent.generate_plots(requested)


@router.post("/features", response_model=FeatureResponse, summary="Suggest feature engineering")
async def features(request: PlotRequest) -> FeatureResponse:
    """Return basic feature engineering suggestions."""
    agent = _agent(request.file_id)
    return agent.suggest_features()

