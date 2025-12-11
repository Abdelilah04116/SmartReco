"""Drilldown endpoint to fetch subset and stats on graph clicks."""
from fastapi import APIRouter, HTTPException, status
import pandas as pd

from models.schemas import DrilldownRequest, DrilldownResponse
from utils import helpers

router = APIRouter(tags=["drilldown"])


@router.post("/drilldown", response_model=DrilldownResponse, summary="Drilldown on a graph selection")
async def drilldown(request: DrilldownRequest) -> DrilldownResponse:
    df = helpers.load_dataframe(request.file_id)
    if request.column not in df.columns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Column not found in dataset")

    series = df[request.column]
    mask = pd.Series([True] * len(df))
    if request.values:
        mask &= series.isin(request.values)
    if request.min_value is not None:
        mask &= series.astype(float) >= request.min_value
    if request.max_value is not None:
        mask &= series.astype(float) <= request.max_value

    subset = df[mask]
    limited = subset.head(request.limit)
    stats = {}
    if pd.api.types.is_numeric_dtype(series):
        stats = {
            "min": float(subset[request.column].min()) if not subset.empty else None,
            "max": float(subset[request.column].max()) if not subset.empty else None,
            "mean": float(subset[request.column].mean()) if not subset.empty else None,
        }

    return DrilldownResponse(
        file_id=request.file_id,
        column=request.column,
        count=len(subset),
        stats=stats,
        rows=limited.replace({pd.NA: None}).to_dict(orient="records"),
    )


