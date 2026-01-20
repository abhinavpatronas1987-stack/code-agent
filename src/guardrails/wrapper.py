"""
Main guardrails wrapper for Code Agent.

This module provides the GuardrailsWrapper class that wraps
the Code Agent with input/output safety checks.

It supports both NeMo Guardrails (if available) and a lightweight
fallback implementation.
"""

import logging
import asyncio
from pathlib import Path
from typing import Any, Optional, Tuple, Generator
from dataclasses import dataclass

# Try to import NeMo Guardrails
try:
    from nemoguardrails import RailsConfig, LLMRails
    from nemoguardrails.actions.actions import ActionResult
    NEMO_AVAILABLE = True
except ImportError:
    NEMO_AVAILABLE = False
    RailsConfig = None
    LLMRails = None

from .config import GuardrailsConfig, get_default_config
from . import actions


logger = logging.getLogger(__name__)


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    passed: bool
    message: Optional[str] = None
    blocked: bool = False
    modified_text: Optional[str] = None


class GuardrailsWrapper:
    """
    Wrapper that adds NeMo Guardrails to the Code Agent.

    This wrapper intercepts input/output and applies safety rails
    without modifying the core Agno agent.

    Features:
        - Input validation (jailbreak, injection, unsafe paths)
        - Output sanitization (secret redaction, command removal)
        - NeMo integration (if installed)
        - Fallback to lightweight checks
        - Async and sync support

    Usage:
        wrapper = GuardrailsWrapper()

        # Check input
        is_safe, error = wrapper.check_input_sync(user_message)

        # Process output
        sanitized = wrapper.process_output_sync(response)
    """

    def __init__(
        self,
        config: Optional[GuardrailsConfig] = None,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize the guardrails wrapper.

        Args:
            config: Guardrails configuration
            config_path: Path to NeMo config directory
        """
        self.config = config or get_default_config()
        self.rails: Optional[Any] = None  # LLMRails when available
        self._initialized = False
        self._nemo_available = NEMO_AVAILABLE

        # Set config for actions module
        actions.set_config(self.config)

        # Initialize NeMo if available and enabled
        if self.config.enabled and NEMO_AVAILABLE:
            self._init_nemo(config_path or self.config.config_path)
        elif self.config.enabled:
            logger.info("NeMo Guardrails not installed, using lightweight checks")

    def _init_nemo(self, config_path: Path) -> None:
        """
        Initialize NeMo Guardrails.

        Args:
            config_path: Path to NeMo configuration directory
        """
        try:
            config_path = Path(config_path)
            if config_path.exists() and (config_path / "config.yml").exists():
                rails_config = RailsConfig.from_path(str(config_path))
                self.rails = LLMRails(rails_config)

                # Register custom actions
                self._register_actions()

                self._initialized = True
                logger.info("NeMo Guardrails initialized successfully")
            else:
                logger.warning(
                    f"NeMo config not found at {config_path}. "
                    "Using lightweight guardrails. "
                    "Create guardrails_config/config.yml to enable NeMo."
                )
        except Exception as e:
            logger.error(f"Failed to initialize NeMo Guardrails: {e}")
            logger.info("Falling back to lightweight guardrails")

    def _register_actions(self) -> None:
        """Register custom actions with NeMo Guardrails."""
        if not self.rails:
            return

        try:
            # Register all action functions
            self.rails.register_action(actions.check_jailbreak_attempt, name="check_jailbreak_attempt")
            self.rails.register_action(actions.check_code_injection, name="check_code_injection")
            self.rails.register_action(actions.check_unsafe_file_path, name="check_unsafe_file_path")
            self.rails.register_action(actions.check_input_safety, name="check_input_safety")
            self.rails.register_action(actions.check_output_safety, name="check_output_safety")
            self.rails.register_action(actions.detect_secrets, name="detect_secrets")
            self.rails.register_action(actions.redact_secrets, name="redact_secrets")
            self.rails.register_action(actions.sanitize_output, name="sanitize_output")
            self.rails.register_action(actions.check_dangerous_code, name="check_dangerous_code")
            logger.debug("Registered custom guardrail actions")
        except Exception as e:
            logger.error(f"Failed to register actions: {e}")

    @property
    def is_enabled(self) -> bool:
        """Check if guardrails are enabled."""
        return self.config.enabled

    @property
    def is_nemo_initialized(self) -> bool:
        """Check if NeMo Guardrails is initialized."""
        return self._initialized and self.rails is not None

    async def check_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Check input through guardrails.

        Args:
            user_input: The user's input message

        Returns:
            Tuple of (is_safe, error_message)
            - is_safe: True if input passed all checks
            - error_message: Description of why input was blocked (if blocked)
        """
        if not self.config.enabled:
            return True, None

        # Use NeMo if initialized
        if self.is_nemo_initialized and self.rails:
            try:
                response = await self.rails.generate_async(
                    messages=[{"role": "user", "content": user_input}]
                )

                # Check if NeMo blocked the request
                if response.get("blocked"):
                    return False, response.get("message", "Input blocked by guardrails")

                # If NeMo didn't block, still run our checks as backup
            except Exception as e:
                logger.error(f"NeMo input check failed: {e}")
                # Fall through to lightweight checks

        # Lightweight checks (always run as backup)
        return await actions.run_all_input_checks(user_input)

    async def process_output(self, output: str) -> str:
        """
        Process and sanitize output through guardrails.

        Args:
            output: The bot's response

        Returns:
            Sanitized output
        """
        if not self.config.enabled:
            return output

        # Run output processing
        return await actions.run_all_output_checks(output)

    def check_input_sync(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Synchronous version of check_input.

        Args:
            user_input: The user's input message

        Returns:
            Tuple of (is_safe, error_message)
        """
        return self._run_async(self.check_input(user_input))

    def process_output_sync(self, output: str) -> str:
        """
        Synchronous version of process_output.

        Args:
            output: The bot's response

        Returns:
            Sanitized output
        """
        return self._run_async(self.process_output(output))

    def _run_async(self, coro):
        """
        Run an async coroutine synchronously.

        Args:
            coro: Coroutine to run

        Returns:
            Result of the coroutine
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists
            return asyncio.run(coro)

    def wrap_response_stream(
        self,
        stream: Generator,
        collect_full_response: bool = True
    ) -> Generator:
        """
        Wrap a streaming response to apply guardrails.

        This allows guardrails to be applied to streaming responses.
        The full response is collected and checked after streaming completes.

        Args:
            stream: Generator yielding response chunks
            collect_full_response: Whether to collect and check full response

        Yields:
            Response chunks (unmodified during streaming)
        """
        full_response = ""

        for chunk in stream:
            # Collect the response
            if collect_full_response and hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content

            yield chunk

        # After streaming, check the full response
        if collect_full_response and full_response:
            processed = self.process_output_sync(full_response)
            if processed != full_response:
                logger.info("Response was sanitized by guardrails")

    def get_status(self) -> dict:
        """
        Get current guardrails status.

        Returns:
            Dict with status information
        """
        return {
            "enabled": self.config.enabled,
            "nemo_available": self._nemo_available,
            "nemo_initialized": self.is_nemo_initialized,
            "input_rails": self.config.input_rails,
            "output_rails": self.config.output_rails,
            "blocked_commands_count": len(self.config.blocked_commands),
            "blocked_paths_count": len(self.config.blocked_paths),
            "secret_patterns_count": len(self.config.secret_patterns),
        }


# ============ SINGLETON MANAGEMENT ============

_guardrails: Optional[GuardrailsWrapper] = None


def get_guardrails(config: Optional[GuardrailsConfig] = None) -> GuardrailsWrapper:
    """
    Get or create the guardrails wrapper singleton.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        GuardrailsWrapper singleton instance
    """
    global _guardrails

    if _guardrails is None:
        _guardrails = GuardrailsWrapper(config=config)

    return _guardrails


def reset_guardrails() -> None:
    """Reset the guardrails singleton (mainly for testing)."""
    global _guardrails
    _guardrails = None


def create_guardrails(config: Optional[GuardrailsConfig] = None) -> GuardrailsWrapper:
    """
    Create a new guardrails instance (not singleton).

    Args:
        config: Optional configuration

    Returns:
        New GuardrailsWrapper instance
    """
    return GuardrailsWrapper(config=config)
