"""Base agent class for all specialized agents."""

from typing import Any

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.db.sqlite import SqliteDb

from src.config.settings import get_settings
from src.core.llm import get_ollama_model


class BaseCodeAgent:
    """
    Base class for creating specialized code agents.

    Provides common functionality:
    - Local LLM integration (Ollama)
    - Persistent storage
    - Tool registration
    - Session management
    """

    def __init__(
        self,
        name: str,
        description: str,
        instructions: list[str],
        tools: list[Any] | None = None,
        model: Ollama | None = None,
        session_id: str | None = None,
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name
            description: Short description of agent's purpose
            instructions: List of instruction strings for the agent
            tools: List of tools the agent can use
            model: LLM model (defaults to Ollama)
            session_id: Session ID for memory persistence
        """
        self.settings = get_settings()
        self.name = name
        self.session_id = session_id or "default"

        # Ensure data directory exists
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)

        # Set up database for agent sessions
        db = SqliteDb(
            db_file=str(self.settings.data_dir / "agent_storage.db"),
        )

        # Build full instructions
        full_instructions = self._build_instructions(instructions)

        # Create the Agno agent
        self.agent = Agent(
            name=name,
            model=model or get_ollama_model(),
            description=description,
            instructions=full_instructions,
            tools=tools or [],
            db=db,
            session_id=self.session_id,
            markdown=True,
            add_datetime_to_context=True,
        )

    def _build_instructions(self, custom_instructions: list[str]) -> list[str]:
        """Build complete instruction set with base instructions."""
        base_instructions = [
            "You are an AI coding assistant in an Agentic Development Environment.",
            "You help developers with coding tasks, terminal commands, and file operations.",
            "Always explain what you're doing before executing commands.",
            "If a task might be destructive, ask for confirmation first.",
            "Use the available tools to interact with the system.",
        ]
        return base_instructions + custom_instructions

    def run(self, message: str, stream: bool = True) -> Any:
        """
        Run the agent with a user message.

        Args:
            message: User's input message
            stream: Whether to stream the response

        Returns:
            Agent response (streamed or complete)
        """
        return self.agent.run(message, stream=stream)

    async def arun(self, message: str, stream: bool = True) -> Any:
        """
        Run the agent asynchronously.

        Args:
            message: User's input message
            stream: Whether to stream the response

        Returns:
            Agent response
        """
        return await self.agent.arun(message, stream=stream)

    def get_history(self) -> list[dict]:
        """Get conversation history for current session."""
        return self.agent.get_history()

    def clear_history(self) -> None:
        """Clear conversation history for current session."""
        self.agent.clear_history()
