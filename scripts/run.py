from pathlib import Path

from pydantic import PostgresDsn

from src.api.config import APISettings
from src.api.file_ingestion.reader import load_file_into_df
from src.api.file_ingestion.service import load_df_into_database

if __name__ == "__main__":
    url = (
        PostgresDsn("postgresql://postgres_user:postgres_password@localhost:5678/postgres_database")
    )
    csv_file_path = Path("/Users/as/code/finance-de/data/data_1.csv")
    excel_file_path = Path("/Users/as/code/finance-de/data/data_2.xlsx")

    df = load_file_into_df(excel_file_path)
    load_df_into_database(
        df,
        APISettings(
            database_url=url,
        ),
    )
