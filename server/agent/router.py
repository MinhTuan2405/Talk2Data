from fastapi import FastAPI
from vanna.servers.fastapi.routes import register_chat_routes

from agent.agent import get_chat_handler
from config import settings


def mount_vanna_routes(app: FastAPI) -> None:
    """Register Vanna 2.0 chat routes onto the FastAPI app.

    Endpoints added:
      POST /api/vanna/v2/chat_sse       (SSE streaming)
      WS   /api/vanna/v2/chat_websocket (WebSocket)
      POST /api/vanna/v2/chat_poll      (polling fallback)
    """
    config = {
        "dev_mode": settings.debug,
        "api_base_url": "",
    }
    register_chat_routes(app, get_chat_handler(), config)
