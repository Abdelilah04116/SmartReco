"""FastAPI application entrypoint for SmartReco."""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Any, Dict, List
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from loguru import logger

from routers import analysis, recommendations, rules, upload, datasets, drilldown, templates, exports
from utils import helpers, dataset_registry

app = FastAPI(title="SmartReco", version="1.0.0")

# Basic CORS to simplify local dev and docker usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(rules.router)
app.include_router(recommendations.router)
app.include_router(datasets.router)
app.include_router(drilldown.router)
app.include_router(templates.router)
app.include_router(exports.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Exception attrapée: {exc!r}\nURL: {request.url}\n", exc_info=True)
    return JSONResponse(status_code=500, content={
        "error": "internal_server_error",
        "detail": str(exc),
        "url": str(request.url)
    })


@app.get("/health")
def health() -> dict[str, object]:
    """Health probe used by Docker and frontend."""
    return {
        "status": "ok",
        "dataset_loaded": helpers.has_any_dataset(),
        "last_file_id": dataset_registry.last_dataset_id() or helpers.get_last_file_id(),
        "dataset_count": dataset_registry.dataset_count(),
        "rules_loaded": 0,
        "scored_count": 0,
    }


@app.get("/")
def root() -> dict[str, str]:
    """Small welcome message."""
    return {"message": "SmartReco backend is running"}


@app.post("/dashboard/generate-fragment")
def generate_dashboard_fragment() -> Dict[str, Any]:
    """
    Generate a simple dashboard fragment based on the last uploaded dataset.

    This is a lightweight implementation to avoid 404 on the dashboard page.
    It builds a few basic widgets from the last uploaded dataset if available.
    """
    file_id = helpers.get_last_file_id()
    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available. Upload a dataset on the Overview page first.",
        )

    df = helpers.load_dataframe(file_id)
    row_count = len(df)
    col_count = len(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    widgets: List[Dict[str, Any]] = [
        {
            "id": "kpi_rows",
            "type": "kpi",
            "title": "Total Lignes",
            "data": {"value": row_count, "trend": "neutral"},
            "config": {"subtitle": "Nombre de lignes", "unit": "rows"},
        },
        {
            "id": "kpi_columns",
            "type": "kpi",
            "title": "Total Colonnes",
            "data": {"value": col_count, "trend": "neutral"},
            "config": {"subtitle": "Colonnes", "unit": "cols"},
        },
    ]

    # Build a bar chart from the first categorical column or a fallback sample
    if cat_cols:
        first_cat = cat_cols[0]
        vc = df[first_cat].value_counts().head(6)
        bar_data = [{"name": str(idx), "value": int(val)} for idx, val in vc.items()]
        widgets.append(
            {
                "id": "bar_top_categories",
                "type": "bar",
                "title": f"Top valeurs de {first_cat}",
                "data": bar_data,
            }
        )

        # Pie chart uses same distribution
        widgets.append(
            {
                "id": "pie_top_categories",
                "type": "pie",
                "title": f"Répartition {first_cat}",
                "data": bar_data,
            }
        )
    elif numeric_cols:
        first_num = numeric_cols[0]
        series = df[first_num].dropna().head(12).reset_index(drop=True)
        line_data = [{"name": f"P{i}", "value": float(val)} for i, val in series.items()]
        widgets.append(
            {
                "id": "line_sample_numeric",
                "type": "line",
                "title": f"Échantillon {first_num}",
                "data": line_data,
            }
        )

    description = "Widgets générés automatiquement à partir du dernier dataset uploadé."
    return {"widgets": widgets, "layout": "auto", "description": description}




