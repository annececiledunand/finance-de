from loguru import logger
import polars as pl

from src.api.config import APISettings
from src.api.file_ingestion.cleaner import (
    extract_and_clean_person,
    extract_and_clean_organization,
    extract_and_clean_job,
)

# ---------------------------------------------------------------------- #
# File and Database Helpers
# ---------------------------------------------------------------------- #


MAPPING_TABLE_NAME_CLEANING = {
    "person": extract_and_clean_person,
    "organization": extract_and_clean_organization,
    "job": extract_and_clean_job,
}

LINK_DATA_WITH_FK_TABLE: dict[str, dict[str, dict[str, tuple[str, ...]]]] = {
    # Table with FK to link
    "job": {
        # referenced table
        "person": {
            # FK key reference of table person to add in table "job": keys in df that will be used for merge and dropped after
            "person_id": ("first_name", "middle_name", "last_name")
        },
        "organization": {"org_id": ("org_name",)},
    },
}


def load_df_into_database(df_data: pl.DataFrame, settings: APISettings) -> dict[str, int]:
    """Load one-table data into database as normalized tables: person, organization, job."""
    created_rows_by_table = {}
    for table_name, clean_method in MAPPING_TABLE_NAME_CLEANING.items():
        logger.info(f"{table_name}: Extraction and cleaning data")
        df_table = clean_method(df_data)

        if table_links_to_add_config := LINK_DATA_WITH_FK_TABLE.get(table_name):
            logger.info(f"{table_name}: FK will be added")
            df_table = add_all_fk_links(
                df_to_link=df_table,
                links=table_links_to_add_config,
                settings=settings,
            )

        created_row_nb = load_df_into_table(
            df_table,
            settings,
            table_name=table_name,
        )
        created_rows_by_table[table_name] = created_row_nb


    return created_rows_by_table


def load_df_into_table(df: pl.DataFrame, settings: APISettings, table_name: str) -> int:
    """Load a df into a table: only insert, will not upsert. If duplicated, will raise an error."""
    logger.info(f"Writing into {table_name} table")
    # todo: batching size, use connection instead of creating new session each time
    rows_inserted = df.write_database(
        table_name=table_name,
        connection=str(settings.database_url),
        if_table_exists="append",
        engine="sqlalchemy",
    )

    logger.success(f"Wrote {rows_inserted} rows into {table_name} table")
    return rows_inserted


def add_all_fk_links(df_to_link: pl.DataFrame, settings: APISettings, links: dict):
    def _add_fk_link(
        _df_to_link: pl.DataFrame, _df_fk: pl.DataFrame, _merge_keys: list[str]
    ) -> pl.DataFrame:
        return _df_to_link.join(
            _df_fk,
            on=_merge_keys,
            how="inner",  # Completely custom since current model enforces not null FKs
        ).drop(*_merge_keys)

    for fk_table, fk_keys_for_link in links.items():
        logger.info(
            f"Add FK link from table {fk_table} with keys {fk_keys_for_link} for join condition"
        )
        join_columns_in_both: list[str] = list(*fk_keys_for_link.values())
        fk_column_to_add = list(fk_keys_for_link.keys())

        # read reference table and select only the columns used for FK + JOIN
        fk_table = pl.read_database_uri(
            query=f"SELECT * FROM {fk_table};",  # !! SQL injection to fix
            uri=str(settings.database_url),
        ).select(*fk_column_to_add, *join_columns_in_both)

        # Add the FK column to the df and drop columns only used for JOIN
        df_to_link = _add_fk_link(
            _df_to_link=df_to_link,
            _df_fk=fk_table,
            _merge_keys=join_columns_in_both,
        )

    return df_to_link
