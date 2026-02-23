from dataclasses import dataclass

from loguru import logger
import polars as pl
from sqlalchemy import insert, text, Table

from src.api.config import APISettings
from src.api.file_ingestion.cleaner import (
    extract_and_clean_person,
    extract_and_clean_organization,
    extract_and_clean_job,
)
from src.api.file_ingestion.constants import PERSON_TABLE, ORGANIZATION_TABLE, JOB_TABLE, LINK_DATA_WITH_FK_TABLE, \
    TableDescriptor
from src.database.engine import get_session_commit

# ---------------------------------------------------------------------- #
# File and Database Helpers
# ---------------------------------------------------------------------- #

MAPPING_TABLE_CLEANING = {
    PERSON_TABLE: extract_and_clean_person,
    ORGANIZATION_TABLE: extract_and_clean_organization,
    JOB_TABLE: extract_and_clean_job,
}


def load_df_into_database(df_data: pl.DataFrame, settings: APISettings) -> dict[str, int]:
    """Load one-table data into database as normalized tables: person, organization, job."""
    created_rows_by_table = {}
    for table, clean_method in MAPPING_TABLE_CLEANING.items():
        logger.info(f"{table.name}: Extraction and cleaning data")
        df_table = clean_method(df_data)

        if table_links_to_add_config := LINK_DATA_WITH_FK_TABLE.get(table.name):
            logger.info(f"{table.name}: FK will be added")
            df_table = add_all_fk_links(
                df_to_link=df_table,
                links=table_links_to_add_config,
                settings=settings,
            )

        created_row_nb = load_df_into_table(
            df_table,
            settings,
            table=table,
        )
        created_rows_by_table[table.name] = created_row_nb


    return created_rows_by_table


def load_df_into_table(df: pl.DataFrame, settings: APISettings, table: TableDescriptor) -> int:
    """Load a df into a table: only insert, will not upsert. If duplicated, will raise an error."""
    logger.info(f"Writing into {table.name} table")
    # todo: batching size, use connection instead of creating new session each time

    # A. If the table is only in INSERT MODE, no conflict declared
    if table.conflict_fields is None:
        return df.write_database(
            table_name=table.name,
            connection=str(settings.database_url),
            if_table_exists="append",  # If conflict will fail
            engine="sqlalchemy",
        )

    # B. If some conflict are possible. To handle upserting (not supported by polars yet),
    # we create first a temp table then, we write raw sql to insert on conflict update
    temp_table_name = f"temp_{table.name}"
    rows_inserted = df.write_database(
        table_name=temp_table_name,
        connection=str(settings.database_url),
        if_table_exists="replace",  # always a new temp table
        engine="sqlalchemy",
    )

    upsert_sql_query = build_upsert_query(table, temp_table_name=temp_table_name)
    with get_session_commit(settings.database_url) as session:
        session.execute(text(upsert_sql_query))

    logger.success(f"Wrote {rows_inserted} rows into {table.name} table")
    return rows_inserted


def build_upsert_query(table: TableDescriptor, temp_table_name: str) -> str:
    table_columns_str = ",".join([*table.conflict_fields, *table.fields_to_update])
    set_columns_statement_str = ",".join(f"{c} = EXCLUDED.{c}" for c in table.fields_to_update)
    conflict_fields_str = ",".join(table.conflict_fields)
    # SQL inejction !!!
    return f"""
    INSERT INTO {table.name} ({table_columns_str})
    SELECT * FROM {temp_table_name}
    ON CONFLICT ({conflict_fields_str}) DO UPDATE SET
        {set_columns_statement_str}
    ;
    """

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
