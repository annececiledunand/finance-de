from functools import lru_cache
from typing import Any

from dotenv import find_dotenv
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = ".env"


class APISettings(BaseSettings):
    """Application settings with environment variable support.

    Attributes:
        database_url: postgresql compatible sql url (postgres://user:pass@localhost:5432/foobar).
        api_version: api version used in the url. api_version=v1 will create .../api/v1/...

    Notes:
        Even when using a dotenv file, pydantic will still read environment variables as well as the dotenv file,
        environment variables will always take priority over values loaded from a dotenv file.
        Cf https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support
    """

    database_url: PostgresDsn | None = Field(default=None)
    api_version: str = "v1"

    # loads from .env file only variables declared here.
    model_config = SettingsConfigDict(env_file=find_dotenv(ENV_FILE), extra="ignore")

    def model_post_init(self, context: Any):
        """Make sure the url of the sql is given in non-local environments."""
        if self.database_url is None:
            raise ValueError("Cannot have an empty database_url")


@lru_cache
def get_api_settings() -> APISettings:
    """Create a cached instance of APISettings and load env variables from file or env directly."""
    return APISettings()
