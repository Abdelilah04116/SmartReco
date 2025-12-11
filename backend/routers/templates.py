"""Dashboard templates endpoints."""
from fastapi import APIRouter

from models.schemas import TemplatesResponse, TemplateDescriptor

router = APIRouter(tags=["templates"])


TEMPLATES = [
    TemplateDescriptor(
        id="kpi",
        name="KPI",
        description="Vue KPI rapide",
        layout={"widgets": ["kpi_rows", "kpi_columns"]},
    ),
    TemplateDescriptor(
        id="sales_marketing",
        name="Sales / Marketing",
        description="Conversions, entonnoir, répartition campagnes",
        layout={"widgets": ["kpi_rows", "bar_top_categories", "pie_top_categories"]},
    ),
    TemplateDescriptor(
        id="risk_churn",
        name="Risk / Churn",
        description="Scores de risque, répartition priorités",
        layout={"widgets": ["kpi_rows", "line_sample_numeric", "bar_top_categories"]},
    ),
]


@router.get("/dashboard/templates", response_model=TemplatesResponse)
async def list_templates() -> TemplatesResponse:
    return TemplatesResponse(templates=TEMPLATES)


