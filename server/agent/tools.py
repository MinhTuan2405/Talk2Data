from vanna.core.registry import ToolRegistry
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
    SaveTextMemoryTool,
)
from vanna.integrations.sqlite import SqliteRunner
from config import settings


def register_tools() -> ToolRegistry:
    db_tool = RunSqlTool(
        sql_runner=SqliteRunner(database_path=settings.sqlite_database_path)
    )

    tools = ToolRegistry()
    tools.register_local_tool(db_tool, access_groups=["admin", "user"])
    tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=["admin"])
    tools.register_local_tool(
        SearchSavedCorrectToolUsesTool(), access_groups=["admin", "user"]
    )
    tools.register_local_tool(
        SaveTextMemoryTool(), access_groups=["admin", "user"]
    )
    tools.register_local_tool(VisualizeDataTool(), access_groups=["admin", "user"])
    return tools
