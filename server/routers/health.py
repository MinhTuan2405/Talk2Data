from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {"message": "TalkWithData API", "status": "running"}


@router.get("/health")
def health():
    return {"status": "ok"}
