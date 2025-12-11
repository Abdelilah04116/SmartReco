"""Dataset listing, history, and restore endpoints."""
from fastapi import APIRouter, HTTPException, status

from models.schemas import DatasetListResponse, FileIdRequest
from utils import dataset_registry, helpers, cache

router = APIRouter(tags=["datasets"])


@router.get("/datasets", response_model=DatasetListResponse, summary="List uploaded datasets")
async def list_datasets() -> DatasetListResponse:
    datasets = dataset_registry.list_datasets()
    return DatasetListResponse(datasets=datasets)


@router.post("/datasets/restore", response_model=dict, summary="Restore cached analysis")
async def restore_cached(payload: FileIdRequest):
    cached = cache.get_cache(payload.file_id)
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cached analysis for this dataset. Please rerun analysis.",
        )
    # Update freshness
    dataset_registry.update_timestamp(payload.file_id)
    return cached


@router.get("/datasets/{file_id}", response_model=dict, summary="Get dataset metadata")
async def dataset_meta(file_id: str):
    meta = dataset_registry.get_dataset(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return meta


