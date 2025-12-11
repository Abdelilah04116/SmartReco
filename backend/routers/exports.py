"""Export endpoints for CSV, Excel, PDF, PNG, and shareable snapshots."""
import base64
import io
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, Response

from models.schemas import FileIdRequest
from utils import helpers, cache

router = APIRouter(tags=["exports"])

# In-memory store for shareable snapshots (in production, use Redis or DB)
_SHARED_SNAPSHOTS: Dict[str, Dict[str, Any]] = {}
_SNAPSHOT_EXPIRY_DAYS = 30


def _generate_share_token() -> str:
    """Generate a unique token for sharing."""
    return uuid.uuid4().hex[:16]


@router.post("/export/csv")
async def export_csv(request: FileIdRequest, table_type: str = Query("recommendations")) -> Response:
    """Export recommendations, rules, or dataset to CSV."""
    df = helpers.load_dataframe(request.file_id)
    
    if table_type == "recommendations":
        cached = cache.get_cache(request.file_id)
        if cached and "recommendations" in cached:
            recs = cached["recommendations"]
            actions = recs.get("actions", [])
            if actions:
                df_export = pd.DataFrame(actions)
            else:
                df_export = pd.DataFrame({"message": ["No recommendations available"]})
        else:
            df_export = pd.DataFrame({"message": ["No recommendations available"]})
    elif table_type == "rules":
        cached = cache.get_cache(request.file_id)
        if cached and "rules" in cached:
            rules = cached["rules"].get("rules", [])
            df_export = pd.DataFrame(rules)
        else:
            df_export = pd.DataFrame({"message": ["No rules available"]})
    else:
        df_export = df
    
    output = io.StringIO()
    df_export.to_csv(output, index=False)
    csv_content = output.getvalue()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="export_{request.file_id[:8]}.csv"'},
    )


@router.post("/export/excel")
async def export_excel(request: FileIdRequest, table_type: str = Query("recommendations")) -> Response:
    """Export to Excel format."""
    df = helpers.load_dataframe(request.file_id)
    
    if table_type == "recommendations":
        cached = cache.get_cache(request.file_id)
        if cached and "recommendations" in cached:
            recs = cached["recommendations"]
            actions = recs.get("actions", [])
            df_export = pd.DataFrame(actions) if actions else pd.DataFrame({"message": ["No recommendations"]})
        else:
            df_export = pd.DataFrame({"message": ["No recommendations available"]})
    elif table_type == "rules":
        cached = cache.get_cache(request.file_id)
        if cached and "rules" in cached:
            rules = cached["rules"].get("rules", [])
            df_export = pd.DataFrame(rules)
        else:
            df_export = pd.DataFrame({"message": ["No rules available"]})
    else:
        df_export = df
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Data")
    
    output.seek(0)
    return Response(
        content=output.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="export_{request.file_id[:8]}.xlsx"'},
    )


@router.post("/export/pdf")
async def export_pdf(request: FileIdRequest, table_type: str = Query("recommendations")) -> Response:
    """Export to PDF (simplified - returns JSON representation for now)."""
    df = helpers.load_dataframe(request.file_id)
    
    if table_type == "recommendations":
        cached = cache.get_cache(request.file_id)
        if cached and "recommendations" in cached:
            recs = cached["recommendations"]
            data = {
                "insights": recs.get("insights", ""),
                "actions": recs.get("actions", []),
                "business_rules": recs.get("business_rules", []),
            }
        else:
            data = {"message": "No recommendations available"}
    elif table_type == "rules":
        cached = cache.get_cache(request.file_id)
        if cached and "rules" in cached:
            data = {"rules": cached["rules"].get("rules", [])}
        else:
            data = {"message": "No rules available"}
    else:
        data = {"rows": df.head(100).to_dict(orient="records")}
    
    # For now, return JSON (in production, use reportlab or weasyprint)
    json_content = json.dumps(data, indent=2, default=str)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="export_{request.file_id[:8]}.json"'},
    )


@router.post("/export/plot/{plot_id}/png")
async def export_plot_png(request: FileIdRequest, plot_id: str) -> Response:
    """Export a specific plot as PNG."""
    cached = cache.get_cache(request.file_id)
    if not cached or "plots" not in cached:
        raise HTTPException(status_code=404, detail="No plots available")
    
    plots = cached["plots"].get("plots", [])
    plot = next((p for p in plots if p.get("title") == plot_id or str(hash(str(p))) == plot_id), None)
    
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    image_base64 = plot.get("image_base64", "")
    if not image_base64:
        raise HTTPException(status_code=404, detail="Plot image not available")
    
    # Decode base64
    image_bytes = base64.b64decode(image_base64)
    
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="plot_{plot_id}.png"'},
    )


@router.post("/share/create")
async def create_share_link(request: FileIdRequest) -> Dict[str, Any]:
    """Create a shareable read-only snapshot link."""
    token = _generate_share_token()
    
    # Gather all cached data for this dataset
    cached = cache.get_cache(request.file_id)
    if not cached:
        raise HTTPException(status_code=404, detail="No analysis data available for sharing")
    
    snapshot = {
        "file_id": request.file_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=_SNAPSHOT_EXPIRY_DAYS)).isoformat(),
        "data": cached,
    }
    
    _SHARED_SNAPSHOTS[token] = snapshot
    
    return {
        "token": token,
        "share_url": f"/share/{token}",
        "expires_at": snapshot["expires_at"],
    }


@router.get("/share/{token}")
async def get_shared_snapshot(token: str) -> Dict[str, Any]:
    """Retrieve a shared snapshot by token."""
    snapshot = _SHARED_SNAPSHOTS.get(token)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    
    expires_at = datetime.fromisoformat(snapshot["expires_at"])
    if datetime.utcnow() > expires_at:
        del _SHARED_SNAPSHOTS[token]
        raise HTTPException(status_code=410, detail="Share link has expired")
    
    return snapshot

