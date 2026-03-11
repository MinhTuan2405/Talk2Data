from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.exceptions import AppException, app_exception_handler
from core.middleware import setup_middleware
from agent.router import mount_vanna_routes
from routers import health
from utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(title="TalkWithData API", lifespan=lifespan)

setup_middleware(app)
app.add_exception_handler(AppException, app_exception_handler)

# --- Vanna 2.0 chat routes (SSE, WebSocket, polling) ---
mount_vanna_routes(app)

# --- Custom routers ---
app.include_router(health.router, tags=["health"])
# app.include_router(xxx.router, prefix="/v1/xxx", tags=["xxx"])


# Only use in the dev environment
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)