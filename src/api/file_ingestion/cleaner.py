from loguru import logger
import polars as pl


def extract_and_clean_person(df: pl.DataFrame) -> pl.DataFrame:
    """From one-table data to person compatible table schema."""
    df_person = df.select(
        "first_name",
        "middle_name",
        "last_name",
        "email",
        "phone",
        "fax",
        "title",
    )

    # prepare data for person
    logger.info("Cleaning data")

    # ## remove duplicates based on names
    logger.info("Drop duplicated person by names")
    df_person = df_person.unique(subset=["first_name", "middle_name", "last_name"])

    # ## Remove extra char in phones after x. Todo: Needs a generic cleaner
    logger.info("Cleaning phone field")
    df_person = df_person.with_columns(
        pl.col("phone").str.split_exact("x", n=0).struct.field("field_0").alias("phone")
    )

    # todo: each line should go into validator and remove each line of error
    return df_person


def extract_and_clean_organization(df: pl.DataFrame) -> pl.DataFrame:
    """From one-table data to organization compatible table schema."""
    df_org = df.select(
        "org_name",
        pl.col("uri").alias("org_vivo_uri"),
    )

    logger.info("Drop duplicated organizations by name and uri")
    df_org = df_org.unique(subset=["org_name", "org_vivo_uri"])

    # todo: verify uri IS an uri and IS also a vivo URI
    return df_org


def extract_and_clean_job(df: pl.DataFrame) -> pl.DataFrame:
    """From one-table data to job compatible table schema."""
    df = df.select(
        # join with "person" table
        "first_name",
        "middle_name",
        "last_name",
        # join with "organization" table
        "org_name",
        # "job" table fields
        "title",
        "start_date",  # todo cast to date
        "job_title",
    ).rename(
        {
            "title": "job_type",
        }
    )

    return df.with_columns(
        # Very ugly: validate length of field and bounds before casting like a maniac
        (pl.col("start_date").cast(pl.String) + "-01-01").str.to_date(),
    )
