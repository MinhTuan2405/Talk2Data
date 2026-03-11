from vanna import Agent
from vanna.core.agent.agent import AgentConfig
from vanna.servers.base import ChatHandler

from agent.llm import get_llm_service
from agent.tools import register_tools
from agent.memory import get_agent_memory
from agent.user_resolver import SimpleUserResolver
from agent.hooks import get_lifecycle_hooks
from agent.middlewares import get_llm_middlewares


_agent: Agent | None = None
_chat_handler: ChatHandler | None = None


def create_agent() -> Agent:
    return Agent(
        llm_service=get_llm_service(),
        tool_registry=register_tools(),
        user_resolver=SimpleUserResolver(),
        agent_memory=get_agent_memory(),
        config=AgentConfig(
            stream_responses=True,
            auto_save_conversations=True,
        ),
        lifecycle_hooks=get_lifecycle_hooks(),
        llm_middlewares=get_llm_middlewares(),
    )


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def get_chat_handler() -> ChatHandler:
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler(agent=get_agent())
    return _chat_handler
