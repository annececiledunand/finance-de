"""Database engine connection infos.

/!\\ Should never reference anything from api.
Imports are made by api from database.
"""

import contextlib
from collections.abc import Generator
from functools import lru_cache

from loguru import logger
from pydantic import PostgresDsn
from sqlalchemy import Engine, text, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


class DBConnectionError(Exception):
    """Raised when database connection fails."""

    pass


def get_session_commit(
    database_url: PostgresDsn,
) -> contextlib.AbstractContextManager[Session]:
    """Create a context manager for giving a database session that will commit after use.

    Args:
        database_url (PostgresDsn): Database connection info.

    Example:
        >>> with get_session_commit("my_url") as my_session:
        >>>    ...
    """

    @contextlib.contextmanager
    def _inner() -> Generator[Session]:
        """Get a database session that will commit after use.

        Yields:
            Generator[Session]: Session generator object to use as context tool.
        """
        engine = get_engine(database_url=database_url)
        with Session(engine) as session:
            yield session
            session.commit()

    return _inner()


@lru_cache(maxsize=1)
def get_engine(database_url: PostgresDsn) -> Engine:
    """Get a database engine object."""
    return create_engine(
        str(database_url),
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before use
    )


def check_db_connection(database_url: PostgresDsn | None) -> None:
    """Raises DBConnectionError if issues, nothing if ok, by executing SELECT 1;

    Args:
        database_url (PostgresDsn): connection url to a postgres database

    Raises:
        DBConnectionError: if database connection fails
    """
    if database_url is None:
        raise ValueError("database_url cannot be None")

    # starts a transaction with "get_session"
    with get_session_commit(database_url) as session:
        try:
            raw_result = session.execute(text("SELECT 1;"))
            result = raw_result.fetchall()
            if result != [(1,)]:
                logger.error(
                    "Database query validation failed", expected=[(1,)], received=result
                )
                raise DBConnectionError(
                    f"Database query returned unexpected result: {result}"
                )
            return
        except OperationalError as error:
            logger.error(f"Error connecting to database.\n{error}")
            raise DBConnectionError(error) from error
