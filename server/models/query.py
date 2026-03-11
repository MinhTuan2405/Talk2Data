from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str | None = None
    result: list | None = None
    error: str | None = None
