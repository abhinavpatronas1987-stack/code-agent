"""
Custom NeMo Guardrails actions for Code Agent.

This module contains all the action functions that are called by
the guardrails system to check input/output safety.

These functions can be used standalone or registered with NeMo Guardrails.
"""

import re
import logging
from typing import Optional, List, Tuple
from pathlib import Path

from .config import GuardrailsConfig, get_default_config


logger = logging.getLogger(__name__)

# Global config instance
_config: Optional[GuardrailsConfig] = None


def set_config(config: GuardrailsConfig) -> None:
    """Set the guardrails configuration."""
    global _config
    _config = config


def get_config() -> GuardrailsConfig:
    """Get current configuration."""
    global _config
    if _config is None:
        _config = get_default_config()
    return _config


# ============ INPUT RAIL ACTIONS ============

async def check_jailbreak_attempt(user_input: str) -> bool:
    """
    Check if input contains jailbreak attempts.

    Args:
        user_input: The user's input text

    Returns:
        True if jailbreak attempt detected, False otherwise
    """
    config = get_config()
    text_lower = user_input.lower()

    for pattern in config.jailbreak_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Jailbreak attempt detected: pattern '{pattern}'")
            return True

    return False


async def check_code_injection(user_input: str) -> bool:
    """
    Check for code injection attempts in user input.

    Args:
        user_input: The user's input text

    Returns:
        True if code injection detected, False otherwise
    """
    config = get_config()
    text_lower = user_input.lower()

    # Check for blocked commands
    for cmd in config.blocked_commands:
        if cmd.lower() in text_lower:
            logger.warning(f"Blocked command detected: '{cmd}'")
            return True

    # Check for injection patterns
    for pattern in config.injection_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Injection pattern detected: '{pattern}'")
            return True

    return False


async def check_unsafe_file_path(user_input: str) -> bool:
    """
    Check for attempts to access unsafe file paths.

    Args:
        user_input: The user's input text

    Returns:
        True if unsafe path detected, False otherwise
    """
    config = get_config()

    # Normalize input for path checking
    text_normalized = user_input.replace("\\", "/").lower()

    for blocked_path in config.blocked_paths:
        normalized_blocked = blocked_path.replace("\\", "/").lower()
        # Handle home directory expansion
        if normalized_blocked.startswith("~"):
            normalized_blocked = normalized_blocked[1:]

        if normalized_blocked in text_normalized:
            logger.warning(f"Blocked path detected: '{blocked_path}'")
            return True

    # Check for path traversal attempts
    traversal_patterns = [
        r"\.\.[/\\]",  # ../
        r"\.\.[/\\]\.\.",  # ../../
        r"%2e%2e[/\\%]",  # URL encoded ../
        r"\.\.%2f",  # Mixed encoding
        r"\.\.%5c",  # Mixed encoding Windows
    ]

    for pattern in traversal_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.warning(f"Path traversal attempt detected")
            return True

    return False


async def check_input_safety(user_input: str) -> bool:
    """
    General input safety check.

    Args:
        user_input: The user's input text

    Returns:
        True if input is unsafe, False otherwise
    """
    config = get_config()

    # Check length
    if len(user_input) > config.max_input_length:
        logger.warning(f"Input too long: {len(user_input)} > {config.max_input_length}")
        return True

    # Check for null bytes (can be used to bypass filters)
    if "\x00" in user_input:
        logger.warning("Null byte detected in input")
        return True

    # Check for excessive special characters (possible obfuscation)
    special_ratio = sum(1 for c in user_input if not c.isalnum() and c not in " \n\t.,!?-_'\"") / max(len(user_input), 1)
    if special_ratio > 0.5:
        logger.warning(f"High special character ratio: {special_ratio:.2f}")
        return True

    return False


# ============ OUTPUT RAIL ACTIONS ============

async def check_output_safety(bot_response: str) -> bool:
    """
    Check if output contains unsafe content.

    Args:
        bot_response: The bot's response text

    Returns:
        True if unsafe content detected, False otherwise
    """
    config = get_config()
    response_lower = bot_response.lower()

    # Check for blocked commands in output
    for cmd in config.blocked_commands:
        if cmd.lower() in response_lower:
            logger.warning(f"Blocked command in output: '{cmd}'")
            return True

    return False


async def detect_secrets(text: str) -> bool:
    """
    Detect if text contains secrets or sensitive data.

    Args:
        text: Text to check for secrets

    Returns:
        True if secrets detected, False otherwise
    """
    config = get_config()

    for pattern in config.secret_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Secret pattern detected")
            return True

    return False


async def redact_secrets(text: str) -> str:
    """
    Redact secrets from text.

    Args:
        text: Text containing secrets

    Returns:
        Text with secrets redacted
    """
    config = get_config()
    result = text

    redaction_map = [
        # API Keys
        (r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([\w\-]{16,})", r"\1=***REDACTED***"),
        (r"(?i)(api[_-]?secret)['\"]?\s*[:=]\s*['\"]?([\w\-]{16,})", r"\1=***REDACTED***"),

        # Passwords
        (r"(?i)(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?([^\s,}\"']{4,})", r"\1=***REDACTED***"),

        # Tokens
        (r"(?i)(secret|token|auth_token)['\"]?\s*[:=]\s*['\"]?([\w\-]{16,})", r"\1=***REDACTED***"),
        (r"(?i)bearer\s+([\w\-\.]{20,})", "Bearer ***REDACTED***"),

        # Provider-specific
        (r"sk-[a-zA-Z0-9]{32,}", "sk-***REDACTED***"),
        (r"sk-proj-[a-zA-Z0-9]{32,}", "sk-proj-***REDACTED***"),
        (r"ghp_[a-zA-Z0-9]{36}", "ghp_***REDACTED***"),
        (r"gho_[a-zA-Z0-9]{36}", "gho_***REDACTED***"),
        (r"AKIA[0-9A-Z]{16}", "AKIA***REDACTED***"),
        (r"AIza[0-9A-Za-z\-_]{35}", "AIza***REDACTED***"),
        (r"xox[baprs]-[0-9a-zA-Z]{10,}", "xox*-***REDACTED***"),
        (r"sk_live_[0-9a-zA-Z]{24,}", "sk_live_***REDACTED***"),
        (r"sk_test_[0-9a-zA-Z]{24,}", "sk_test_***REDACTED***"),

        # Connection strings
        (r"(?i)(mongodb|postgres|mysql|redis)://([^:]+):([^@]+)@", r"\1://\2:***REDACTED***@"),

        # Private keys
        (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
         "-----BEGIN PRIVATE KEY-----\n***REDACTED***\n-----END PRIVATE KEY-----"),
    ]

    for pattern, replacement in redaction_map:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


async def sanitize_output(text: str) -> str:
    """
    Sanitize output by removing unsafe content.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    config = get_config()
    result = text

    # Remove blocked commands
    for cmd in config.blocked_commands:
        if cmd.lower() in result.lower():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(cmd), re.IGNORECASE)
            result = pattern.sub("[BLOCKED COMMAND]", result)

    return result


async def check_dangerous_code(code: str) -> bool:
    """
    Check if generated code contains dangerous operations.

    Args:
        code: Code to check

    Returns:
        True if dangerous code detected, False otherwise
    """
    dangerous_patterns = [
        # Python dangerous functions
        (r"subprocess\.call\([^)]*shell\s*=\s*True", "subprocess with shell=True"),
        (r"subprocess\.Popen\([^)]*shell\s*=\s*True", "Popen with shell=True"),
        (r"os\.system\(", "os.system()"),
        (r"os\.popen\(", "os.popen()"),
        (r"(?<![\w.])eval\(", "eval()"),
        (r"(?<![\w.])exec\(", "exec()"),
        (r"__import__\(", "__import__()"),
        (r"importlib\.import_module\(", "dynamic import"),
        (r"pickle\.loads?\(", "pickle deserialization"),
        (r"yaml\.load\([^)]*(?!Loader\s*=\s*yaml\.SafeLoader)", "unsafe YAML load"),
        (r"marshal\.loads?\(", "marshal deserialization"),

        # JavaScript dangerous patterns
        (r"(?<![\w.])eval\(", "eval()"),
        (r"new\s+Function\(", "new Function()"),
        (r"innerHTML\s*=", "innerHTML assignment"),
        (r"document\.write\(", "document.write()"),

        # SQL injection risks
        (r"f['\"].*\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE|DROP)", "SQL with f-string"),
        (r"\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE|DROP)", "SQL with .format()"),
        (r"\+.*(?:SELECT|INSERT|UPDATE|DELETE|DROP)", "SQL string concatenation"),

        # Shell command construction
        (r"f['\"].*\{.*\}.*(?:rm|del|format|sudo)", "shell command with f-string"),
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            logger.warning(f"Dangerous code pattern detected: {description}")
            return True

    return False


# ============ SYNCHRONOUS WRAPPERS ============

def check_jailbreak_attempt_sync(user_input: str) -> bool:
    """Synchronous version of check_jailbreak_attempt."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(check_jailbreak_attempt(user_input))


def check_code_injection_sync(user_input: str) -> bool:
    """Synchronous version of check_code_injection."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(check_code_injection(user_input))


def check_unsafe_file_path_sync(user_input: str) -> bool:
    """Synchronous version of check_unsafe_file_path."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(check_unsafe_file_path(user_input))


def redact_secrets_sync(text: str) -> str:
    """Synchronous version of redact_secrets."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(redact_secrets(text))


# ============ COMBINED CHECK FUNCTIONS ============

async def run_all_input_checks(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Run all input checks and return result.

    Args:
        user_input: User input to check

    Returns:
        Tuple of (is_safe, error_message)
    """
    # Check jailbreak
    if await check_jailbreak_attempt(user_input):
        return False, "I cannot help with that request. I'm designed to assist with legitimate coding tasks only."

    # Check code injection
    if await check_code_injection(user_input):
        return False, "Potentially dangerous command detected. Please rephrase your request without destructive operations."

    # Check file paths
    if await check_unsafe_file_path(user_input):
        return False, "Cannot access system directories or sensitive paths. Please specify a safe working directory."

    # Check general safety
    if await check_input_safety(user_input):
        return False, "Input validation failed. Please check your request and try again."

    return True, None


async def run_all_output_checks(output: str) -> str:
    """
    Run all output checks and return sanitized output.

    Args:
        output: Bot output to process

    Returns:
        Sanitized output
    """
    result = output

    # Redact secrets
    if await detect_secrets(result):
        result = await redact_secrets(result)

    # Sanitize unsafe content
    if await check_output_safety(result):
        result = await sanitize_output(result)

    return result
