from pydantic import BaseModel


class TrainingDataCreate(BaseModel):
    question: str
    sql: str
    ddl: str | None = None


class TrainingDataResponse(BaseModel):
    id: str
    question: str
    sql: str
