from vanna.integrations.anthropic import AnthropicLlmService
from config import settings


def get_llm_service() -> AnthropicLlmService:
    return AnthropicLlmService(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
    )
