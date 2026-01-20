"""Core module - LLM and agent base components."""

from src.core.llm import get_ollama_model
from src.core.base_agent import BaseCodeAgent

__all__ = ["get_ollama_model", "BaseCodeAgent"]
