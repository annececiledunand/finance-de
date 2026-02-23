from collections.abc import Generator
from contextlib import AbstractContextManager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.api.config import APISettings, get_api_settings
from src.database.engine import get_session_commit


def get_session(
    settings: Annotated[APISettings, Depends(get_api_settings)],
) -> Generator[Session]:
    """FastAPI dependency for a SQLAlchemy.Session object with transaction,
    where the database url is loaded from settings (themselves a dependency)."""
    with get_session_from_settings(settings) as session:
        yield session


def get_session_from_settings(settings: APISettings) -> AbstractContextManager[Session]:
    """Get session for the database defined in the api settings."""
    if settings.database_url is None:
        raise RuntimeError(
            "database_url from settings is required to connect to database"
        )

    return get_session_commit(settings.database_url)
