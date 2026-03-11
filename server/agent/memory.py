from vanna.integrations.local.agent_memory import DemoAgentMemory


def get_agent_memory() -> DemoAgentMemory:
    return DemoAgentMemory(max_items=1000)
