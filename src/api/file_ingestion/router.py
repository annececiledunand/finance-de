from pathlib import Path

from fastapi import APIRouter, Path as FastAPIPath, HTTPException
from fastapi.params import Depends, Annotated

from src.api.config import APISettings, get_api_settings
from src.api.file_ingestion.reader import load_file_into_df
from src.api.file_ingestion.schemas import FileIngestionResponse
from src.api.file_ingestion.service import load_df_into_database

file_ingestion_router = APIRouter()


@file_ingestion_router.post(
    "/upload",
    description="Main entry point for file_ingestion",
    tags=["file_ingestion"],
)
def file_ingestion_endpoint(
    file_path: str,
    settings: Annotated[APISettings, Depends(get_api_settings)],
) -> FileIngestionResponse:
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    df_data = load_file_into_df(file_path=Path(file_path))
    results = load_df_into_database(df_data, settings)
    return FileIngestionResponse(
        **{table: {"created": nb_created} for table, nb_created in results.items()},
    )