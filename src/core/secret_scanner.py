"""Secret Scanner - Feature 22.

Detect exposed secrets in code:
- API keys
- Passwords
- Tokens
- Private keys
- Connection strings
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class SecretType(Enum):
    """Types of secrets."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    CONNECTION_STRING = "connection_string"
    AWS_KEY = "aws_key"
    GENERIC = "generic"


class Severity(Enum):
    """Severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SecretFinding:
    """A detected secret."""
    file_path: str
    line_number: int
    line_content: str
    secret_type: SecretType
    severity: Severity
    pattern_name: str
    matched_text: str
    recommendation: str


@dataclass
class ScanResult:
    """Result of a secret scan."""
    files_scanned: int = 0
    secrets_found: int = 0
    findings: List[SecretFinding] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class SecretScanner:
    """Scanner for detecting secrets in code."""

    # Secret patterns with severity
    PATTERNS = {
        # AWS
        "aws_access_key": {
            "pattern": r"(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "type": SecretType.AWS_KEY,
            "severity": Severity.CRITICAL,
            "description": "AWS Access Key ID",
        },
        "aws_secret_key": {
            "pattern": r"(?i)aws[_\-]?secret[_\-]?(?:access[_\-]?)?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})",
            "type": SecretType.AWS_KEY,
            "severity": Severity.CRITICAL,
            "description": "AWS Secret Access Key",
        },
        # API Keys
        "generic_api_key": {
            "pattern": r"(?i)(?:api[_\-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?",
            "type": SecretType.API_KEY,
            "severity": Severity.HIGH,
            "description": "Generic API Key",
        },
        "openai_api_key": {
            "pattern": r"sk-[A-Za-z0-9]{48}",
            "type": SecretType.API_KEY,
            "severity": Severity.CRITICAL,
            "description": "OpenAI API Key",
        },
        "anthropic_api_key": {
            "pattern": r"sk-ant-[A-Za-z0-9\-]{40,}",
            "type": SecretType.API_KEY,
            "severity": Severity.CRITICAL,
            "description": "Anthropic API Key",
        },
        "github_token": {
            "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}",
            "type": SecretType.TOKEN,
            "severity": Severity.CRITICAL,
            "description": "GitHub Token",
        },
        "github_oauth": {
            "pattern": r"(?i)github[_\-]?(?:oauth|token)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_]{35,})",
            "type": SecretType.TOKEN,
            "severity": Severity.CRITICAL,
            "description": "GitHub OAuth Token",
        },
        "slack_token": {
            "pattern": r"xox[baprs]-[A-Za-z0-9\-]{10,}",
            "type": SecretType.TOKEN,
            "severity": Severity.HIGH,
            "description": "Slack Token",
        },
        "stripe_key": {
            "pattern": r"(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{24,}",
            "type": SecretType.API_KEY,
            "severity": Severity.CRITICAL,
            "description": "Stripe API Key",
        },
        "google_api_key": {
            "pattern": r"AIza[A-Za-z0-9_\-]{35}",
            "type": SecretType.API_KEY,
            "severity": Severity.HIGH,
            "description": "Google API Key",
        },
        # Passwords
        "password_assignment": {
            "pattern": r"(?i)(?:password|passwd|pwd)['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
            "type": SecretType.PASSWORD,
            "severity": Severity.HIGH,
            "description": "Password in code",
        },
        "password_url": {
            "pattern": r"(?i)://[^:]+:([^@]{8,})@",
            "type": SecretType.PASSWORD,
            "severity": Severity.HIGH,
            "description": "Password in URL",
        },
        # Private Keys
        "private_key_rsa": {
            "pattern": r"-----BEGIN (?:RSA )?PRIVATE KEY-----",
            "type": SecretType.PRIVATE_KEY,
            "severity": Severity.CRITICAL,
            "description": "RSA Private Key",
        },
        "private_key_openssh": {
            "pattern": r"-----BEGIN OPENSSH PRIVATE KEY-----",
            "type": SecretType.PRIVATE_KEY,
            "severity": Severity.CRITICAL,
            "description": "OpenSSH Private Key",
        },
        "private_key_ec": {
            "pattern": r"-----BEGIN EC PRIVATE KEY-----",
            "type": SecretType.PRIVATE_KEY,
            "severity": Severity.CRITICAL,
            "description": "EC Private Key",
        },
        # Tokens
        "jwt_token": {
            "pattern": r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
            "type": SecretType.TOKEN,
            "severity": Severity.MEDIUM,
            "description": "JWT Token",
        },
        "bearer_token": {
            "pattern": r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}",
            "type": SecretType.TOKEN,
            "severity": Severity.HIGH,
            "description": "Bearer Token",
        },
        # Connection Strings
        "database_url": {
            "pattern": r"(?i)(?:mysql|postgres|postgresql|mongodb|redis)://[^\s'\"]+",
            "type": SecretType.CONNECTION_STRING,
            "severity": Severity.HIGH,
            "description": "Database Connection String",
        },
        # Generic secrets
        "secret_assignment": {
            "pattern": r"(?i)(?:secret|token)[_\-]?(?:key)?['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-]{16,})['\"]",
            "type": SecretType.GENERIC,
            "severity": Severity.MEDIUM,
            "description": "Generic Secret",
        },
    }

    # Files to skip
    SKIP_EXTENSIONS = {
        ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
        ".woff", ".woff2", ".ttf", ".eot",
        ".zip", ".tar", ".gz", ".rar",
        ".pdf", ".doc", ".docx",
    }

    SKIP_DIRS = {
        ".git", ".svn", ".hg",
        "node_modules", ".venv", "venv", "__pycache__",
        ".pytest_cache", ".mypy_cache",
        "dist", "build", ".next", ".nuxt",
    }

    # Files that commonly have false positives
    ALLOWLIST_FILES = {
        "package-lock.json", "yarn.lock", "poetry.lock",
        "Pipfile.lock", "composer.lock",
    }

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize secret scanner."""
        self.working_dir = working_dir or Path.cwd()

    def scan(
        self,
        path: Optional[Path] = None,
        patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ScanResult:
        """
        Scan for secrets.

        Args:
            path: Path to scan (default: working_dir)
            patterns: Only check these patterns (default: all)
            exclude_patterns: Skip these patterns

        Returns:
            ScanResult with findings
        """
        scan_path = path or self.working_dir
        result = ScanResult()

        # Get patterns to use
        active_patterns = self.PATTERNS.copy()
        if patterns:
            active_patterns = {k: v for k, v in active_patterns.items() if k in patterns}
        if exclude_patterns:
            active_patterns = {k: v for k, v in active_patterns.items() if k not in exclude_patterns}

        # Scan files
        if scan_path.is_file():
            files = [scan_path]
        else:
            files = self._get_files(scan_path)

        for file_path in files:
            result.files_scanned += 1
            findings = self._scan_file(file_path, active_patterns)
            result.findings.extend(findings)

        # Count by severity
        result.secrets_found = len(result.findings)
        for finding in result.findings:
            if finding.severity == Severity.CRITICAL:
                result.critical_count += 1
            elif finding.severity == Severity.HIGH:
                result.high_count += 1
            elif finding.severity == Severity.MEDIUM:
                result.medium_count += 1
            else:
                result.low_count += 1

        return result

    def _get_files(self, directory: Path) -> List[Path]:
        """Get all files to scan."""
        files = []

        for item in directory.rglob("*"):
            # Skip directories in skip list
            if any(skip_dir in item.parts for skip_dir in self.SKIP_DIRS):
                continue

            if item.is_file():
                # Skip by extension
                if item.suffix.lower() in self.SKIP_EXTENSIONS:
                    continue

                # Skip allowlisted files
                if item.name in self.ALLOWLIST_FILES:
                    continue

                files.append(item)

        return files

    def _scan_file(
        self,
        file_path: Path,
        patterns: Dict[str, Dict],
    ) -> List[SecretFinding]:
        """Scan a single file for secrets."""
        findings = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                # Skip empty lines and comments
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                    continue

                # Check each pattern
                for pattern_name, pattern_info in patterns.items():
                    matches = re.finditer(pattern_info["pattern"], line)

                    for match in matches:
                        # Skip if looks like a placeholder/example
                        matched_text = match.group(0)
                        if self._is_placeholder(matched_text):
                            continue

                        finding = SecretFinding(
                            file_path=str(file_path.relative_to(self.working_dir)),
                            line_number=line_num,
                            line_content=line[:200],  # Truncate long lines
                            secret_type=pattern_info["type"],
                            severity=pattern_info["severity"],
                            pattern_name=pattern_name,
                            matched_text=self._mask_secret(matched_text),
                            recommendation=self._get_recommendation(pattern_info["type"]),
                        )
                        findings.append(finding)

        except Exception:
            pass  # Skip files that can't be read

        return findings

    def _is_placeholder(self, text: str) -> bool:
        """Check if text looks like a placeholder."""
        placeholders = [
            "xxx", "yyy", "zzz", "your_", "my_", "example",
            "placeholder", "changeme", "replace", "insert",
            "todo", "fixme", "<", ">", "${", "{{",
            "test", "dummy", "fake", "sample",
        ]
        text_lower = text.lower()
        return any(p in text_lower for p in placeholders)

    def _mask_secret(self, text: str) -> str:
        """Mask a secret for display."""
        if len(text) <= 8:
            return "*" * len(text)
        return text[:4] + "*" * (len(text) - 8) + text[-4:]

    def _get_recommendation(self, secret_type: SecretType) -> str:
        """Get recommendation for a secret type."""
        recommendations = {
            SecretType.API_KEY: "Use environment variables or a secrets manager",
            SecretType.PASSWORD: "Use environment variables, never hardcode passwords",
            SecretType.TOKEN: "Store tokens in environment variables or secure storage",
            SecretType.PRIVATE_KEY: "Never commit private keys, use secrets manager",
            SecretType.CONNECTION_STRING: "Use environment variables for connection strings",
            SecretType.AWS_KEY: "Use IAM roles or AWS Secrets Manager",
            SecretType.GENERIC: "Move sensitive data to environment variables",
        }
        return recommendations.get(secret_type, "Remove or secure this secret")

    def scan_file(self, file_path: Path) -> List[SecretFinding]:
        """Scan a single file."""
        return self._scan_file(file_path, self.PATTERNS)

    def get_report(self, result: ScanResult) -> str:
        """Generate scan report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  SECRET SCANNER REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(f"Files Scanned: {result.files_scanned}")
        lines.append(f"Secrets Found: {result.secrets_found}")
        lines.append("")

        if result.secrets_found > 0:
            lines.append("Severity Breakdown:")
            if result.critical_count:
                lines.append(f"  [CRITICAL] {result.critical_count}")
            if result.high_count:
                lines.append(f"  [HIGH]     {result.high_count}")
            if result.medium_count:
                lines.append(f"  [MEDIUM]   {result.medium_count}")
            if result.low_count:
                lines.append(f"  [LOW]      {result.low_count}")
            lines.append("")

            # Findings
            lines.append("Findings:")
            lines.append("-" * 60)

            for finding in result.findings:
                severity_marker = {
                    Severity.CRITICAL: "[!!!]",
                    Severity.HIGH: "[!!]",
                    Severity.MEDIUM: "[!]",
                    Severity.LOW: "[.]",
                }[finding.severity]

                lines.append(f"\n{severity_marker} {finding.pattern_name}")
                lines.append(f"    File: {finding.file_path}:{finding.line_number}")
                lines.append(f"    Type: {finding.secret_type.value}")
                lines.append(f"    Match: {finding.matched_text}")
                lines.append(f"    Recommendation: {finding.recommendation}")

        else:
            lines.append("[OK] No secrets detected!")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_scanner: Optional[SecretScanner] = None


def get_secret_scanner(working_dir: Optional[Path] = None) -> SecretScanner:
    """Get or create secret scanner."""
    global _scanner
    if _scanner is None:
        _scanner = SecretScanner(working_dir)
    return _scanner


# Convenience functions
def scan_secrets(path: Optional[Path] = None) -> ScanResult:
    """Scan for secrets."""
    return get_secret_scanner().scan(path)


def scan_file_for_secrets(file_path: Path) -> List[SecretFinding]:
    """Scan a single file for secrets."""
    return get_secret_scanner().scan_file(file_path)
