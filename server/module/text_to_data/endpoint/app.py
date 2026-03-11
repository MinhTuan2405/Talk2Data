from fastapi import APIRouter
from vanna import Agent
from vanna.servers.base import ChatHandler
from vanna.servers.fastapi.routes import register_chat_routes

from module.text_to_data.config import VANNA_DEV_MODE
from module.text_to_data.service.llm.llm import create_llm_service
from module.text_to_data.service.tool.tool import create_tool_registry
from module.text_to_data.service.agent_memory.agent_memory import create_agent_memory
from module.text_to_data.service.user_resolver import JWTUserResolver


def create_vanna_server():
    app = APIRouter()

    llm_service = create_llm_service()
    tool_registry = create_tool_registry()
    agent_memory = create_agent_memory()
    user_resolver = JWTUserResolver()

    agent = Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
    )

    chat_handler = ChatHandler(agent)
    register_chat_routes(app, chat_handler, config={
        "dev_mode": VANNA_DEV_MODE,
        "cdn_url": "https://img.vanna.ai/vanna-components.js",
    })

    return app
