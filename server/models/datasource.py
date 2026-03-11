from pydantic import BaseModel


class DatasourceCreate(BaseModel):
    name: str
    connection_string: str
    db_type: str = "sqlite"


class DatasourceResponse(BaseModel):
    id: str
    name: str
    db_type: str
    status: str = "connected"
