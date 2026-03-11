from vanna.core.registry import ToolRegistry
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
    SaveTextMemoryTool,
)
from vanna.integrations.postgres import PostgresRunner

from module.text_to_data.config import SQL_DATABASE_URL


def create_tool_registry() -> ToolRegistry:
    """Create and configure the tool registry with SQL, visualization, and memory tools."""
    db_tool = RunSqlTool(
        sql_runner=PostgresRunner(connection_string=SQL_DATABASE_URL)
    )

    registry = ToolRegistry()
    registry.register_local_tool(db_tool, access_groups=["admin", "user"])
    registry.register_local_tool(VisualizeDataTool(), access_groups=["admin", "user"])
    registry.register_local_tool(SaveQuestionToolArgsTool(), access_groups=["admin"])
    registry.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=["admin", "user"])
    registry.register_local_tool(SaveTextMemoryTool(), access_groups=["admin", "user"])

    return registry
