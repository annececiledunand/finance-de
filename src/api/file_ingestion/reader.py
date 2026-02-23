from pathlib import Path
from loguru import logger
import polars as pl


def load_file_into_df(file_path: Path):
    """Handles only CSV and Excel file formats."""
    logger.info(f"Reading file {file_path}")

    if file_path.suffix == ".csv":
        return load_csv_into_df(csv_file_path=file_path)

    if file_path.suffix == ".xlsx":
        return load_excel_into_df(excel_file_path=file_path)

    raise NotImplementedError("Unsupported file format")


# ------------------------------------------------------------------ #
# CSV
# ------------------------------------------------------------------ #

CSV_MAPPING_COLUMN_NAMES = {
    "dataFirstNames": "first_names",
    "dataLastName": "last_name",
    "dataEmail": "email",
    "dataPhone": "phone",
    "dataFax": "fax",
    "dataTitle": "title",
    "dataJobTitle": "job_title",
    "dataPositionType": "position_type",
    "dataOrganization": "org_name",
    "dataJobStartDate": "start_date",
    "dataURI": "uri",
}


def load_csv_into_df(csv_file_path: Path) -> pl.DataFrame:
    logger.info(f"Reading csv file {csv_file_path}")
    df = pl.read_csv(csv_file_path, separator=";")

    df = df.rename(CSV_MAPPING_COLUMN_NAMES)
    return _csv_create_middle_name_field(df)


def _csv_create_middle_name_field(df: pl.DataFrame) -> pl.DataFrame:
    """Specific to CSV origin file"""
    logger.info("Extracting first_name and middle_name fields from first_names")
    return (
        df.with_columns(
            pl.col("first_names")
            .str.split_exact(", ", 1)
            .struct.rename_fields(["first_name", "middle_name"])
            .alias("field_name_fields")
        )
        .unnest("field_name_fields")
        .drop("first_names")
    )


# ------------------------------------------------------------------ #
# EXCEL
# ------------------------------------------------------------------ #

EXCEL_COLUMN_MAPPING_NAMES = {
    "raw_first": "first_name",
    "raw_last": "last_name",
    "raw_middle": "middle_name",
    "raw_email": "email",
    "raw_phone": "phone",
    "raw_fax": "fax",
    "raw_title": "title",
    "raw_job_title": "job_title",
    "raw_position_type": "position_type",
    "raw_org_name": "org_name",
    "raw_date": "start_date",
    "raw_uri": "uri",
}


def load_excel_into_df(excel_file_path: Path) -> pl.DataFrame:
    logger.info(f"Reading excel file {excel_file_path}")
    df = pl.read_excel(excel_file_path)

    return df.rename(EXCEL_COLUMN_MAPPING_NAMES)
