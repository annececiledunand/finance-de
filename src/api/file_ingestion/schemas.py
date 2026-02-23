from pydantic import BaseModel

class TableActionStat(BaseModel):
    created: int = 0
    updated: int = 0
    ignored: int = 0

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "created": "1",
                    "updated": "0",
                    "ignored": "0",
                },
            ]
        },
    }

class FileIngestionResponse(BaseModel):
    person: TableActionStat
    organization: TableActionStat
    job: TableActionStat
