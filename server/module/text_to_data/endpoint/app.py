from fastapi import FastAPI, APIRouter
from vanna import Agent
from vanna.servers.base import ChatHandler
from vanna.servers.fastapi.routes import register_chat_routes


def create_vanna_server ():
    # existing FastAPI app with your own routes
    app = APIRouter()

    # ... existing routes here ...
    # @app.get("/api/users")
    # @app.post("/api/orders")
    # etc.

    # Add Vanna chat endpoints to your existing app
    agent = Agent(
        # llm_service=llm,
        # tool_registry=registry,
        # user_resolver=user_resolver,
        # agent_memory=agent_memory
    )

    chat_handler = ChatHandler(agent)
    register_chat_routes(app, chat_handler, config={
        "dev_mode": False,
        "cdn_url": "https://img.vanna.ai/vanna-components.js"
    })

    return app
