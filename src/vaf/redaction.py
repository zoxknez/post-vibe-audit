"""
VAF Redaction Module — Secrets Firewall

Detects and masks secrets/credentials before sending context to an LLM.
Never logs actual secret values. Generates a secrets_report.json
with counts and types only.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ─── Secret patterns ───────────────────────────────────────────────────────────
# Each pattern has: name, regex, replacement mask

@dataclass
class SecretPattern:
    name: str
    pattern: re.Pattern[str]
    mask: str = "***REDACTED***"


# fmt: off
_PATTERNS: list[SecretPattern] = [
    # OpenAI
    SecretPattern("openai_api_key",
        re.compile(r'(sk-(?:proj-)?[A-Za-z0-9]{20,})', re.IGNORECASE),
        "sk-***REDACTED***"),

    # Anthropic Claude
    SecretPattern("anthropic_api_key",
        re.compile(r'(sk-ant-[A-Za-z0-9\-_]{20,})', re.IGNORECASE),
        "sk-ant-***REDACTED***"),

    # Google / GCP
    SecretPattern("google_api_key",
        re.compile(r'(AIza[0-9A-Za-z\-_]{35})', re.IGNORECASE),
        "AIza***REDACTED***"),
    SecretPattern("gcp_service_account",
        re.compile(r'"private_key":\s*"-----BEGIN PRIVATE KEY-----[^"]*"', re.DOTALL),
        '"private_key": "***REDACTED***"'),

    # GitHub
    SecretPattern("github_token",
        re.compile(r'(ghp_[A-Za-z0-9]{32,40}|github_pat_[A-Za-z0-9_]{82})', re.IGNORECASE),
        "ghp_***REDACTED***"),
    SecretPattern("github_oauth",
        re.compile(r'(gho_[A-Za-z0-9]{32,40})', re.IGNORECASE),
        "gho_***REDACTED***"),

    # GitLab
    SecretPattern("gitlab_token",
        re.compile(r'(glpat-[A-Za-z0-9\-_]{20})', re.IGNORECASE),
        "glpat-***REDACTED***"),

    # AWS
    SecretPattern("aws_access_key",
        re.compile(r'(AKIA[0-9A-Z]{16})', re.IGNORECASE),
        "AKIA***REDACTED***"),
    SecretPattern("aws_secret_key",
        re.compile(
            r'(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*["\']?([A-Za-z0-9/+]{40})["\']?',
            re.IGNORECASE,
        ),
        "***REDACTED_AWS_SECRET***"),

    # Azure
    SecretPattern("azure_connection_string",
        re.compile(
            r'(DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]+)',
            re.IGNORECASE,
        ),
        "DefaultEndpointsProtocol=https;AccountName=***;AccountKey=***REDACTED***"),

    # JWT / Bearer tokens
    SecretPattern("jwt_token",
        re.compile(
            r'(?:Bearer\s+)(eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,})',
            re.IGNORECASE,
        ),
        "Bearer eyJ***REDACTED***"),
    SecretPattern("jwt_raw",
        re.compile(r'(eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,})'),
        "eyJ***REDACTED***"),

    # Generic password in config
    SecretPattern("password_in_config",
        re.compile(
            r'(?:password|passwd|pwd|secret)\s*[=:]\s*["\']([^"\']{8,})["\']',
            re.IGNORECASE,
        ),
        r'***REDACTED_PASSWORD***'),

    # Database connection strings
    SecretPattern("db_connection_string",
        re.compile(
            r'((?:postgresql|mysql|mongodb|redis|amqp)://[^:]+:[^@]{4,}@[^\s"\']+)',
            re.IGNORECASE,
        ),
        "***REDACTED_DB_URL***"),

    # Generic private key
    SecretPattern("private_key_pem",
        re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', re.DOTALL),
        "-----BEGIN PRIVATE KEY-----\n***REDACTED***\n-----END PRIVATE KEY-----"),

    # Stripe
    SecretPattern("stripe_key",
        re.compile(r'(sk_(?:live|test)_[A-Za-z0-9]{24,})', re.IGNORECASE),
        "sk_***REDACTED***"),
    SecretPattern("stripe_webhook",
        re.compile(r'(whsec_[A-Za-z0-9]{32,})', re.IGNORECASE),
        "whsec_***REDACTED***"),

    # Twilio
    SecretPattern("twilio_auth_token",
        re.compile(r'(AC[a-z0-9]{32})', re.IGNORECASE),
        "AC***REDACTED***"),

    # Sendgrid
    SecretPattern("sendgrid_api_key",
        re.compile(r'(SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43})', re.IGNORECASE),
        "SG.***REDACTED***"),

    # Slack
    SecretPattern("slack_token",
        re.compile(r'(xox[baprs]-[A-Za-z0-9\-]{10,})', re.IGNORECASE),
        "xox***REDACTED***"),

    # Mailchimp
    SecretPattern("mailchimp_key",
        re.compile(r'([0-9a-f]{32}-us[0-9]+)', re.IGNORECASE),
        "***REDACTED_MAILCHIMP***"),
]
# fmt: on


# ─── Entropy check (for generic high-entropy strings) ─────────────────────────

def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for c in s:
        counts[c] = counts.get(c, 0) + 1
    length = len(s)
    return -sum((cnt / length) * math.log2(cnt / length) for cnt in counts.values())


_HIGH_ENTROPY_PATTERN = re.compile(
    r'(?:api_?key|secret|token|auth|credential|password)\s*[=:]\s*["\']?([A-Za-z0-9+/=_\-]{20,})["\']?',
    re.IGNORECASE,
)
_ENTROPY_THRESHOLD = 4.0  # bits — reasonable threshold for secrets


# ─── Finding and Report types ──────────────────────────────────────────────────

@dataclass
class RedactionFinding:
    pattern_name: str
    file_path: str
    line_number: int
    redacted: bool = True
    # We intentionally do NOT store the actual matched value


@dataclass
class RedactionReport:
    total_files_scanned: int = 0
    total_secrets_found: int = 0
    findings: list[RedactionFinding] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_files_scanned": self.total_files_scanned,
            "total_secrets_found": self.total_secrets_found,
            "findings": [
                {
                    "pattern_name": f.pattern_name,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "redacted": f.redacted,
                    "value": "***REDACTED — never stored***",
                }
                for f in self.findings
            ],
        }


# ─── Core redaction function ───────────────────────────────────────────────────

def redact_content(
    content: str,
    file_path: str = "<unknown>",
    report: RedactionReport | None = None,
) -> str:
    """
    Apply all secret patterns to content and return redacted version.
    Optionally accumulates findings into a RedactionReport.

    Args:
        content: Raw file content to redact.
        file_path: Source file path (used only for reporting, not for matching).
        report: If provided, appends findings to this report.

    Returns:
        Redacted content string. Never returns actual secret values.
    """
    result = content

    for sp in _PATTERNS:
        matches = list(sp.pattern.finditer(result))
        if matches:
            result = sp.pattern.sub(sp.mask, result)
            if report is not None:
                for match in matches:
                    line_number = content[: match.start()].count("\n") + 1
                    report.total_secrets_found += 1
                    report.findings.append(
                        RedactionFinding(
                            pattern_name=sp.name,
                            file_path=file_path,
                            line_number=line_number,
                        )
                    )

    # High-entropy generic check
    for match in _HIGH_ENTROPY_PATTERN.finditer(result):
        value = match.group(1)
        if _shannon_entropy(value) >= _ENTROPY_THRESHOLD:
            result = result.replace(match.group(0), match.group(0).replace(value, "***REDACTED_HIGH_ENTROPY***"))
            if report is not None:
                line_number = content[: match.start()].count("\n") + 1
                report.total_secrets_found += 1
                report.findings.append(
                    RedactionFinding(
                        pattern_name="high_entropy_generic",
                        file_path=file_path,
                        line_number=line_number,
                    )
                )

    return result


def redact_file(file_path: Path, report: RedactionReport | None = None) -> str:
    """
    Read a file and return redacted content.

    Args:
        file_path: Path to the file to redact.
        report: Optional report to accumulate findings.

    Returns:
        Redacted file content as string.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    if report is not None:
        report.total_files_scanned += 1

    return redact_content(content, str(file_path), report)


def save_secrets_report(report: RedactionReport, output_path: Path) -> None:
    """
    Save secrets report to JSON. Report contains only metadata — never actual values.

    Args:
        report: RedactionReport to serialize.
        output_path: Path to write JSON file.
    """
    output_path.write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ─── Quick scan (check without full redaction) ─────────────────────────────────

def has_secrets(content: str) -> bool:
    """Quick check: does content contain any known secret patterns?"""
    for sp in _PATTERNS:
        if sp.pattern.search(content):
            return True
    for match in _HIGH_ENTROPY_PATTERN.finditer(content):
        if _shannon_entropy(match.group(1)) >= _ENTROPY_THRESHOLD:
            return True
    return False


def fingerprint_redacted(content: str) -> str:
    """
    Return a SHA-256 fingerprint of redacted content.
    Useful for deduplication without storing actual secrets.
    """
    return hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
