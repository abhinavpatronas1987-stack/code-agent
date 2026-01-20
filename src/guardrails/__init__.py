"""
Guardrails module for Code Agent security.

This module provides NeMo Guardrails integration for input/output safety,
jailbreak detection, command injection prevention, and secret redaction.

Usage:
    from src.guardrails import get_guardrails, GuardrailsConfig

    # Get guardrails instance (singleton)
    guardrails = get_guardrails()

    # Check input
    is_safe, error_msg = guardrails.check_input_sync(user_input)

    # Process output
    sanitized = guardrails.process_output_sync(response)
"""

from .config import GuardrailsConfig, get_default_config
from .wrapper import GuardrailsWrapper, get_guardrails
from .actions import (
    check_jailbreak_attempt,
    check_code_injection,
    check_unsafe_file_path,
    check_input_safety,
    check_output_safety,
    detect_secrets,
    redact_secrets,
    sanitize_output,
    check_dangerous_code,
)

__all__ = [
    # Main classes
    "GuardrailsWrapper",
    "GuardrailsConfig",
    # Factory functions
    "get_guardrails",
    "get_default_config",
    # Action functions
    "check_jailbreak_attempt",
    "check_code_injection",
    "check_unsafe_file_path",
    "check_input_safety",
    "check_output_safety",
    "detect_secrets",
    "redact_secrets",
    "sanitize_output",
    "check_dangerous_code",
]

__version__ = "1.0.0"
