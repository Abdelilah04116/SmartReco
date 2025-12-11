"""Upload and dataset preview endpoints."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from models.schemas import DatasetPreviewResponse, UploadResponse
from utils import helpers
from utils import dataset_registry

router = APIRouter(tags=["upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV file",
)
async def upload_dataset(file: UploadFile = File(...)) -> UploadResponse:
    """Accept any CSV file, detect encoding, persist temporarily, and return a preview."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    file_id, encoding, delimiter, has_header = helpers.save_upload_file(file)
    df = helpers.load_dataframe(file_id)
    preview = helpers.get_preview(df)

    dataset_registry.register_dataset(
        file_id,
        name=helpers.get_registered_file_name(file_id),
        path=str(helpers.get_path(file_id)),
        encoding=encoding,
        rows=len(df),
        columns=len(df.columns),
        delimiter=delimiter,
        has_header=has_header,
        detected_types={col: str(dtype) for col, dtype in df.dtypes.items()},
    )

    return UploadResponse(
        file_id=file_id,
        original_filename=helpers.get_registered_file_name(file_id),
        rows=preview["rows"],
        dtypes=preview["dtypes"],
        columns=preview["columns"],
        delimiter=delimiter,
        has_header=has_header,
        created_at=dataset_registry.get_dataset(file_id)["created_at"],
    )


@router.get(
    "/dataset",
    response_model=DatasetPreviewResponse,
    summary="Retrieve dataset preview",
)
async def get_dataset(file_id: str) -> DatasetPreviewResponse:
    """Return a preview for a previously uploaded dataset."""
    df = helpers.load_dataframe(file_id)
    preview = helpers.get_preview(df)
    return DatasetPreviewResponse(
        file_id=file_id, rows=preview["rows"], dtypes=preview["dtypes"], columns=preview["columns"]
    )




