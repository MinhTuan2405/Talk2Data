from vanna.core.agent.agent import LlmMiddleware


# Example:
# class RequestLoggingMiddleware(LlmMiddleware):
#     async def before_llm_request(self, request):
#         print(f"LLM request: {request}")
#         return request
#
#     async def after_llm_response(self, request, response):
#         return response


def get_llm_middlewares() -> list[LlmMiddleware]:
    return []
