"""LLM integration supporting Ollama and Anthropic Claude."""

from agno.models.ollama import Ollama
from agno.models.anthropic import Claude

from src.config.settings import get_settings


def get_ollama_model(
    model_id: str | None = None,
    temperature: float = 0.1,
) -> Ollama:
    """
    Get an Ollama model instance for the agent.

    Args:
        model_id: Model to use (defaults to settings.ollama_model)
        temperature: Sampling temperature (lower = more deterministic)

    Returns:
        Configured Ollama model instance
    """
    settings = get_settings()

    return Ollama(
        id=model_id or settings.ollama_model,
        host=settings.ollama_base_url,
        options={
            "temperature": temperature,
            "num_ctx": 32768,  # Context window
            "num_predict": 4096,  # Max tokens to generate
        },
        timeout=300.0,  # 5 minute timeout for long operations
    )


def get_anthropic_model(
    model_id: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> Claude:
    """
    Get an Anthropic Claude model instance for the agent.

    Args:
        model_id: Model to use (defaults to settings.anthropic_model)
        temperature: Sampling temperature (defaults to settings.anthropic_temperature)
        max_tokens: Max tokens to generate (defaults to settings.anthropic_max_tokens)

    Returns:
        Configured Claude model instance
    """
    settings = get_settings()

    return Claude(
        id=model_id or settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=temperature if temperature is not None else settings.anthropic_temperature,
        max_tokens=max_tokens if max_tokens is not None else settings.anthropic_max_tokens,
    )


def get_model(model_id: str | None = None):
    """
    Get the configured LLM model based on settings.

    Uses llm_provider setting to determine which provider to use.

    Args:
        model_id: Optional model ID override

    Returns:
        Configured model instance (Ollama or Claude)
    """
    settings = get_settings()

    if settings.llm_provider == "anthropic":
        return get_anthropic_model(model_id=model_id)
    else:
        return get_ollama_model(model_id=model_id)


def get_embedding_model() -> Ollama:
    """Get Ollama model for embeddings."""
    settings = get_settings()

    return Ollama(
        id=settings.ollama_embedding_model,
        host=settings.ollama_base_url,
    )
