from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20
