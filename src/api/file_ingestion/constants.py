from dataclasses import dataclass


@dataclass(frozen=True) # needs to be hashable to be a dict key
class TableDescriptor:
    name: str
    fields_to_update: tuple[str, ...] | None = None
    conflict_fields: tuple[str, ...] | None = None


PERSON_TABLE = TableDescriptor(
    "person",
    fields_to_update=("email", "phone", "fax", "title"),
    conflict_fields=("first_name", "middle_name", "last_name"),
)

ORGANIZATION_TABLE = TableDescriptor(
    "organization",
    conflict_fields=("org_name", ),
    fields_to_update=("org_vivo_uri",),
)

JOB_TABLE = TableDescriptor(
    "job",
) # only append strategy


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
