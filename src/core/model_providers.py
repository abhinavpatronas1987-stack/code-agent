"""Multi-Model Provider Support - Feature 5.

Supports multiple LLM providers:
- Ollama (local)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Groq (fast inference)
- OpenRouter (multiple models)
"""

import os
from enum import Enum
from typing import Optional, Any, Dict
from dataclasses import dataclass

from src.config.settings import get_settings


class ModelProvider(Enum):
    """Supported model providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    OPENROUTER = "openrouter"


@dataclass
class ModelConfig:
    """Configuration for a model."""
    provider: ModelProvider
    model_id: str
    display_name: str
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    context_window: int = 8192
    max_tokens: int = 4096
    supports_streaming: bool = True
    supports_functions: bool = True
    cost_per_1k_input: float = 0.0  # USD
    cost_per_1k_output: float = 0.0


# Available models registry
AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    # Ollama (Local)
    "ollama/gpt-oss:20b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="gpt-oss:20b",
        display_name="GPT-OSS 20B (Local)",
        context_window=32768,
        max_tokens=4096,
    ),
    "ollama/llama3:8b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="llama3:8b",
        display_name="Llama 3 8B (Local)",
        context_window=8192,
        max_tokens=4096,
    ),
    "ollama/llama3:70b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="llama3:70b",
        display_name="Llama 3 70B (Local)",
        context_window=8192,
        max_tokens=4096,
    ),
    "ollama/codellama:13b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="codellama:13b",
        display_name="Code Llama 13B (Local)",
        context_window=16384,
        max_tokens=4096,
    ),
    "ollama/deepseek-coder:6.7b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="deepseek-coder:6.7b",
        display_name="DeepSeek Coder 6.7B (Local)",
        context_window=16384,
        max_tokens=4096,
    ),
    "ollama/qwen2.5-coder:7b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="qwen2.5-coder:7b",
        display_name="Qwen 2.5 Coder 7B (Local)",
        context_window=32768,
        max_tokens=4096,
    ),
    "ollama/mistral:7b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="mistral:7b",
        display_name="Mistral 7B (Local)",
        context_window=8192,
        max_tokens=4096,
    ),

    # OpenAI
    "openai/gpt-4o": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o (OpenAI)",
        api_key_env="OPENAI_API_KEY",
        context_window=128000,
        max_tokens=4096,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
    ),
    "openai/gpt-4o-mini": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini (OpenAI)",
        api_key_env="OPENAI_API_KEY",
        context_window=128000,
        max_tokens=4096,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    "openai/gpt-4-turbo": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo (OpenAI)",
        api_key_env="OPENAI_API_KEY",
        context_window=128000,
        max_tokens=4096,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
    ),
    "openai/gpt-3.5-turbo": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo (OpenAI)",
        api_key_env="OPENAI_API_KEY",
        context_window=16385,
        max_tokens=4096,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
    ),

    # Anthropic
    "anthropic/claude-3-5-sonnet": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet (Anthropic)",
        api_key_env="ANTHROPIC_API_KEY",
        context_window=200000,
        max_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "anthropic/claude-3-opus": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-opus-20240229",
        display_name="Claude 3 Opus (Anthropic)",
        api_key_env="ANTHROPIC_API_KEY",
        context_window=200000,
        max_tokens=4096,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
    ),
    "anthropic/claude-3-haiku": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-haiku-20240307",
        display_name="Claude 3 Haiku (Anthropic)",
        api_key_env="ANTHROPIC_API_KEY",
        context_window=200000,
        max_tokens=4096,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
    ),

    # Google
    "google/gemini-pro": ModelConfig(
        provider=ModelProvider.GOOGLE,
        model_id="gemini-pro",
        display_name="Gemini Pro (Google)",
        api_key_env="GOOGLE_API_KEY",
        context_window=32000,
        max_tokens=8192,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
    ),
    "google/gemini-1.5-pro": ModelConfig(
        provider=ModelProvider.GOOGLE,
        model_id="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro (Google)",
        api_key_env="GOOGLE_API_KEY",
        context_window=1000000,
        max_tokens=8192,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
    ),

    # Groq (Fast inference)
    "groq/llama3-70b": ModelConfig(
        provider=ModelProvider.GROQ,
        model_id="llama3-70b-8192",
        display_name="Llama 3 70B (Groq - Fast)",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        context_window=8192,
        max_tokens=4096,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079,
    ),
    "groq/mixtral-8x7b": ModelConfig(
        provider=ModelProvider.GROQ,
        model_id="mixtral-8x7b-32768",
        display_name="Mixtral 8x7B (Groq - Fast)",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        context_window=32768,
        max_tokens=4096,
        cost_per_1k_input=0.00027,
        cost_per_1k_output=0.00027,
    ),

    # OpenRouter (Access to many models)
    "openrouter/auto": ModelConfig(
        provider=ModelProvider.OPENROUTER,
        model_id="openrouter/auto",
        display_name="Auto-Select Best (OpenRouter)",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        context_window=128000,
        max_tokens=4096,
    ),
}


def get_api_key(env_var: str) -> Optional[str]:
    """Get API key from environment."""
    return os.environ.get(env_var)


def check_model_availability(model_key: str) -> Dict[str, Any]:
    """Check if a model is available (API key present, etc.)."""
    if model_key not in AVAILABLE_MODELS:
        return {"available": False, "reason": "Model not found"}

    config = AVAILABLE_MODELS[model_key]

    # Ollama models - check if Ollama is running
    if config.provider == ModelProvider.OLLAMA:
        try:
            import httpx
            settings = get_settings()
            response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if config.model_id in model_names or any(config.model_id.split(":")[0] in m for m in model_names):
                    return {"available": True, "status": "installed"}
                return {"available": False, "reason": f"Model not installed. Run: ollama pull {config.model_id}"}
            return {"available": False, "reason": "Ollama not responding"}
        except Exception as e:
            return {"available": False, "reason": f"Ollama error: {e}"}

    # Cloud models - check API key
    if config.api_key_env:
        api_key = get_api_key(config.api_key_env)
        if api_key:
            return {"available": True, "status": "api_key_set"}
        return {"available": False, "reason": f"No API key. Set {config.api_key_env}"}

    return {"available": True, "status": "unknown"}


def list_available_models() -> Dict[str, Dict]:
    """List all models with their availability status."""
    result = {}
    for key, config in AVAILABLE_MODELS.items():
        availability = check_model_availability(key)
        result[key] = {
            "display_name": config.display_name,
            "provider": config.provider.value,
            "model_id": config.model_id,
            "context_window": config.context_window,
            "available": availability.get("available", False),
            "status": availability.get("status") or availability.get("reason"),
            "cost_input": config.cost_per_1k_input,
            "cost_output": config.cost_per_1k_output,
        }
    return result


def get_model(model_key: str, temperature: float = 0.1) -> Any:
    """
    Get a model instance by key.

    Args:
        model_key: Model key like "ollama/llama3:8b" or "openai/gpt-4o"
        temperature: Sampling temperature

    Returns:
        Model instance compatible with Agno
    """
    if model_key not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model_key}. Use list_available_models() to see options.")

    config = AVAILABLE_MODELS[model_key]
    settings = get_settings()

    if config.provider == ModelProvider.OLLAMA:
        from agno.models.ollama import Ollama
        return Ollama(
            id=config.model_id,
            host=settings.ollama_base_url,
            options={
                "temperature": temperature,
                "num_ctx": config.context_window,
                "num_predict": config.max_tokens,
            },
            timeout=300.0,
        )

    elif config.provider == ModelProvider.OPENAI:
        from agno.models.openai import OpenAIChat
        api_key = get_api_key(config.api_key_env)
        if not api_key:
            raise ValueError(f"OpenAI API key not set. Set {config.api_key_env} environment variable.")
        return OpenAIChat(
            id=config.model_id,
            api_key=api_key,
            temperature=temperature,
            max_tokens=config.max_tokens,
        )

    elif config.provider == ModelProvider.ANTHROPIC:
        from agno.models.anthropic import Claude
        api_key = get_api_key(config.api_key_env)
        if not api_key:
            raise ValueError(f"Anthropic API key not set. Set {config.api_key_env} environment variable.")
        return Claude(
            id=config.model_id,
            api_key=api_key,
            temperature=temperature,
            max_tokens=config.max_tokens,
        )

    elif config.provider == ModelProvider.GOOGLE:
        from agno.models.google import Gemini
        api_key = get_api_key(config.api_key_env)
        if not api_key:
            raise ValueError(f"Google API key not set. Set {config.api_key_env} environment variable.")
        return Gemini(
            id=config.model_id,
            api_key=api_key,
            temperature=temperature,
        )

    elif config.provider == ModelProvider.GROQ:
        from agno.models.groq import Groq
        api_key = get_api_key(config.api_key_env)
        if not api_key:
            raise ValueError(f"Groq API key not set. Set {config.api_key_env} environment variable.")
        return Groq(
            id=config.model_id,
            api_key=api_key,
            temperature=temperature,
            max_tokens=config.max_tokens,
        )

    elif config.provider == ModelProvider.OPENROUTER:
        from agno.models.openai import OpenAIChat
        api_key = get_api_key(config.api_key_env)
        if not api_key:
            raise ValueError(f"OpenRouter API key not set. Set {config.api_key_env} environment variable.")
        return OpenAIChat(
            id=config.model_id,
            api_key=api_key,
            base_url=config.base_url,
            temperature=temperature,
            max_tokens=config.max_tokens,
        )

    else:
        raise ValueError(f"Unsupported provider: {config.provider}")


def get_default_model_key() -> str:
    """Get the default model key based on settings."""
    settings = get_settings()
    return f"ollama/{settings.ollama_model}"


# Quick aliases
def get_fast_model(temperature: float = 0.1):
    """Get a fast model for simple tasks."""
    # Try Groq first (fastest), then local
    for key in ["groq/mixtral-8x7b", "ollama/llama3:8b", "ollama/mistral:7b"]:
        availability = check_model_availability(key)
        if availability.get("available"):
            return get_model(key, temperature)
    return get_model(get_default_model_key(), temperature)


def get_smart_model(temperature: float = 0.1):
    """Get the smartest available model for complex tasks."""
    # Try best models in order
    for key in ["anthropic/claude-3-5-sonnet", "openai/gpt-4o", "ollama/llama3:70b", "ollama/gpt-oss:20b"]:
        availability = check_model_availability(key)
        if availability.get("available"):
            return get_model(key, temperature)
    return get_model(get_default_model_key(), temperature)
