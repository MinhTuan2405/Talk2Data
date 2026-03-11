from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.openai import OpenAILlmService
from vanna.integrations.google import GeminiLlmService
from vanna.integrations.ollama import OllamaLlmService

from module.text_to_data.config import LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, OLLAMA_BASE_URL


def create_llm_service():
    """Create LLM service based on configured provider."""
    provider = LLM_PROVIDER.lower()

    if provider == "ollama":
        return OllamaLlmService(
            model=LLM_MODEL,
            host=OLLAMA_BASE_URL,
        )
    elif provider == "openai":
        return OpenAILlmService(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
        )
    elif provider == "anthropic":
        return AnthropicLlmService(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
        )
    elif provider == "google":
        return GeminiLlmService(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")