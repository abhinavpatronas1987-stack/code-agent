"""
Guardrails configuration for Code Agent.

This module defines all configurable settings for the guardrails system,
including blocked commands, file paths, and secret patterns.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import os


@dataclass
class GuardrailsConfig:
    """
    Configuration for NeMo Guardrails integration.

    Attributes:
        enabled: Whether guardrails are active
        config_path: Path to NeMo config directory
        input_rails: List of input rail names to enable
        output_rails: List of output rail names to enable
        blocked_commands: Shell commands to block
        blocked_paths: File paths to block access to
        secret_patterns: Regex patterns for secrets to redact
        max_input_length: Maximum allowed input length
        log_blocked_requests: Whether to log blocked requests
        log_file: Path to log file (optional)
    """

    # Enable/disable guardrails
    enabled: bool = True

    # Path to NeMo config directory
    config_path: Path = field(default_factory=lambda: Path("guardrails_config"))

    # Input rails to enable
    input_rails: List[str] = field(default_factory=lambda: [
        "check_jailbreak",
        "check_code_injection",
        "check_file_path_safety",
        "check_input_safety",
    ])

    # Output rails to enable
    output_rails: List[str] = field(default_factory=lambda: [
        "check_output_safety",
        "check_sensitive_data",
        "check_code_safety",
    ])

    # Blocked commands (terminal safety) - DANGEROUS OPERATIONS
    blocked_commands: List[str] = field(default_factory=lambda: [
        # Unix/Linux destructive commands
        "rm -rf /",
        "rm -rf /*",
        "rm -rf ~",
        "rm -rf .",
        "sudo rm -rf",
        "> /dev/sda",
        "> /dev/hda",
        "dd if=/dev/zero",
        "dd if=/dev/random",
        "mkfs.",
        "mkfs.ext",
        ":(){:|:&};:",  # Fork bomb
        "chmod -R 777 /",
        "chown -R",

        # Windows destructive commands
        "format c:",
        "format d:",
        "del /f /s /q c:",
        "del /f /s /q *",
        "rd /s /q c:",
        "rd /s /q",

        # Database destructive
        "DROP DATABASE",
        "DROP TABLE",
        "TRUNCATE TABLE",
        "DELETE FROM",  # Without WHERE

        # Network attacks
        "nc -e",  # Netcat reverse shell
        "bash -i >& /dev/tcp",
        "python -c 'import socket",
    ])

    # Blocked file paths - SENSITIVE LOCATIONS
    blocked_paths: List[str] = field(default_factory=lambda: [
        # Unix system files
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/ssh",
        "/root/",
        "/var/log/auth",

        # User sensitive directories
        "~/.ssh",
        "~/.gnupg",
        "~/.aws",
        "~/.azure",
        "~/.gcloud",
        "~/.kube",
        "~/.docker",

        # Environment and secrets
        ".env",
        ".env.local",
        ".env.production",
        "credentials.json",
        "secrets.yml",
        "secrets.yaml",
        ".netrc",
        ".npmrc",
        ".pypirc",

        # Windows system
        "C:\\Windows\\System32",
        "C:\\Windows\\system.ini",
        "C:\\Users\\*\\AppData",
    ])

    # Patterns to redact from output - SECRETS
    secret_patterns: List[str] = field(default_factory=lambda: [
        # API Keys (generic)
        r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?[\w\-]{16,}",
        r"(?i)(api[_-]?secret)['\"]?\s*[:=]\s*['\"]?[\w\-]{16,}",

        # Passwords
        r"(?i)(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?[^\s,}\"']{4,}",
        r"(?i)(db_password|database_password)['\"]?\s*[:=]\s*['\"]?[^\s,}\"']+",

        # Tokens and Secrets
        r"(?i)(secret|token|auth_token)['\"]?\s*[:=]\s*['\"]?[\w\-]{16,}",
        r"(?i)(access_token|refresh_token)['\"]?\s*[:=]\s*['\"]?[\w\-\.]{20,}",
        r"(?i)bearer\s+[\w\-\.]{20,}",

        # Provider-specific keys
        r"sk-[a-zA-Z0-9]{32,}",  # OpenAI keys
        r"sk-proj-[a-zA-Z0-9]{32,}",  # OpenAI project keys
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub personal tokens
        r"gho_[a-zA-Z0-9]{36}",  # GitHub OAuth tokens
        r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}",  # GitHub fine-grained
        r"AKIA[0-9A-Z]{16}",  # AWS Access Key
        r"(?i)aws[_-]?secret[_-]?access[_-]?key['\"]?\s*[:=]\s*['\"]?[\w/+=]{40}",
        r"AIza[0-9A-Za-z\-_]{35}",  # Google API Key
        r"ya29\.[0-9A-Za-z\-_]+",  # Google OAuth
        r"xox[baprs]-[0-9a-zA-Z]{10,}",  # Slack tokens
        r"sk_live_[0-9a-zA-Z]{24,}",  # Stripe live key
        r"sk_test_[0-9a-zA-Z]{24,}",  # Stripe test key
        r"SG\.[a-zA-Z0-9]{22}\.[a-zA-Z0-9]{43}",  # SendGrid
        r"[0-9a-f]{32}-us[0-9]{1,2}",  # Mailchimp

        # Private keys
        r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        r"-----BEGIN PGP PRIVATE KEY BLOCK-----",

        # Connection strings
        r"(?i)(mongodb|postgres|mysql|redis)://[^\s]+@[^\s]+",
        r"(?i)jdbc:[a-z]+://[^\s]+",
    ])

    # Maximum input length (characters)
    max_input_length: int = 100000

    # Jailbreak detection patterns
    jailbreak_patterns: List[str] = field(default_factory=lambda: [
        r"ignore (all )?(previous |prior )?instructions",
        r"disregard (all )?(previous |prior )?(instructions|rules|guidelines)",
        r"forget (all )?(previous |prior )?(instructions|rules|context)",
        r"you are now (a |an )?(?!coding|code|software|developer|programming)",
        r"pretend (you are|to be) (a |an )?(?!coding|developer|programmer)",
        r"act as (a |an )?(?!coding|developer|programmer|assistant)",
        r"from now on,? you (are|will be)",
        r"new persona",
        r"switch (to )?(a )?new (mode|persona|character)",
        r"DAN mode",
        r"developer mode",
        r"jailbreak",
        r"bypass (your |the )?(safety|restrictions|filters|rules)",
        r"override (your |the )?(safety|restrictions|programming)",
        r"do anything now",
        r"no restrictions",
        r"unlocked mode",
        r"hypothetically,? (if you |you )?(could|were|had)",
    ])

    # Code injection patterns
    injection_patterns: List[str] = field(default_factory=lambda: [
        r";\s*(rm|del|format|dd|mkfs|chmod|chown)",
        r"\|\s*(rm|del|format|bash|sh|cmd)",
        r"&&\s*(rm|del|format|sudo)",
        r"`[^`]*(rm|del|format|sudo)[^`]*`",  # Backtick command substitution
        r"\$\([^)]*(rm|del|format|sudo)[^)]*\)",  # $() command substitution
        r">\s*/dev/(sda|hda|null)",
        r"curl\s+[^|]*\|\s*(bash|sh)",  # Pipe to shell
        r"wget\s+[^|]*\|\s*(bash|sh)",
    ])

    # Logging settings
    log_blocked_requests: bool = True
    log_file: Optional[Path] = None

    @classmethod
    def from_env(cls) -> "GuardrailsConfig":
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv("GUARDRAILS_ENABLED", "true").lower() == "true",
            config_path=Path(os.getenv("GUARDRAILS_CONFIG_PATH", "guardrails_config")),
            max_input_length=int(os.getenv("GUARDRAILS_MAX_INPUT", "100000")),
            log_blocked_requests=os.getenv("GUARDRAILS_LOG_BLOCKED", "true").lower() == "true",
        )


def get_default_config() -> GuardrailsConfig:
    """Get default guardrails configuration."""
    return GuardrailsConfig()


def get_config_from_env() -> GuardrailsConfig:
    """Get configuration from environment variables."""
    return GuardrailsConfig.from_env()
