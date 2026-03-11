from vanna.integrations.local.agent_memory import DemoAgentMemory

from module.text_to_data.config import AGENT_MEMORY_MAX_ITEMS


def create_agent_memory():
    """Create agent memory for storing question-answer pairs and text memories."""
    return DemoAgentMemory(max_items=AGENT_MEMORY_MAX_ITEMS)
