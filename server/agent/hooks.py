from vanna.core.agent.agent import LifecycleHook


# Example:
# class LoggingHook(LifecycleHook):
#     async def before_message(self, user, message):
#         print(f"[{user.email}] {message}")
#         return message
#
#     async def after_tool(self, result):
#         return result


def get_lifecycle_hooks() -> list[LifecycleHook]:
    return []
