"""Main entry point for Code Agent."""

import sys


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "serve":
            # Run the API server
            from src.api.server import run_server
            run_server()

        elif command == "cli":
            # Run the CLI
            sys.argv = sys.argv[1:]  # Remove 'cli' from args
            from src.cli import run_cli
            run_cli()

        elif command in ["-h", "--help", "help"]:
            print_help()

        else:
            # Assume it's a workspace path, run CLI
            from src.cli import run_cli
            run_cli()

    else:
        # Default: run CLI
        from src.cli import run_cli
        run_cli()


def print_help():
    """Print help message."""
    print("""
Code Agent - Agentic Development Environment

Usage:
    python main.py [command] [options]

Commands:
    cli [workspace]     Run interactive CLI (default)
    serve               Run API server

Examples:
    python main.py                      # Start CLI in current directory
    python main.py cli ./my-project     # Start CLI in specific directory
    python main.py serve                # Start API server

Environment:
    Make sure Ollama is running with a model loaded:
    > ollama run qwen2.5-coder:7b
""")


if __name__ == "__main__":
    main()
