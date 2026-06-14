"""
VAF Configuration — loads and validates vaf.config.yaml, with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ─── Default values ────────────────────────────────────────────────────────────

DEFAULT_EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".next", "build", "dist", "out", ".vibe_audit", "bin", "obj",
    ".idea", ".vscode", ".gemini", "artifacts", "scratch", "coverage",
    "htmlcov", ".pytest_cache", ".mypy_cache", ".ruff_cache", "target",
    ".gradle", ".mvn", "vendor", "tmp", ".terraform", ".serverless",
    "coverage-html", "jmeter-report-dir", "locust-output",
}

DEFAULT_EXCLUDE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "CURRENT_CONTEXT.md", ".DS_Store", "Thumbs.db",
    # Never pack secrets:
    ".env", ".env.local", ".env.production", ".env.staging",
    ".env.development", ".env.test",
}

DEFAULT_ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".scss",
    ".md", ".toml", ".yaml", ".yml", ".sql", ".sh", ".bat", ".ps1",
    ".rs", ".go", ".c", ".cpp", ".h", ".cs", ".java", ".kt", ".swift",
    ".graphql", ".gql", ".prisma", ".hcl", ".tf", ".proto",
    ".dockerfile", ".nginx", ".conf", ".ini", ".xml", ".env.example",
}

DEFAULT_SPECIAL_FILES = {
    "Dockerfile", "Makefile", "Procfile", "CODEOWNERS",
    "pyproject.toml", "requirements.txt", "requirements-dev.txt",
    "package.json", "tsconfig.json", "jest.config.js", "jest.config.ts",
    ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintignore",
    ".prettierrc", "sonar-project.properties", "bandit.yaml",
    "trivy.yaml", ".bandit", "locust.conf",
}


# ─── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class LimitsConfig:
    max_total_files: int = 300
    max_file_size_kb: int = 200
    max_total_tokens: int = 150_000


@dataclass
class OutputConfig:
    formats: list[str] = field(default_factory=lambda: ["markdown"])
    directory: str = ".vibe_audit"


@dataclass
class StandardsConfig:
    web: list[str] = field(default_factory=lambda: [
        "OWASP_TOP_10_2025",
        "OWASP_ASVS_5",
        "OWASP_API_TOP_10_2023",
    ])
    ai: list[str] = field(default_factory=lambda: [
        "OWASP_LLM_TOP_10_2025",
        "OWASP_AGENTIC_TOP_10_2026",
    ])
    supply_chain: list[str] = field(default_factory=lambda: [
        "SLSA",
        "OpenSSF_SCORECARD",
        "SBOM",
    ])
    privacy: list[str] = field(default_factory=lambda: [
        "GDPR",
    ])


@dataclass
class GateConfig:
    local: str = "critical"
    pr: str = "high"
    staging: str = "high"
    production: str = "medium"


@dataclass
class VAFConfig:
    """Complete VAF configuration."""

    version: int = 1
    language: str = "sr-Latn"
    mode: str = "deep"

    # Limits
    limits: LimitsConfig = field(default_factory=LimitsConfig)

    # Output
    output: OutputConfig = field(default_factory=OutputConfig)

    # Standards
    standards: StandardsConfig = field(default_factory=StandardsConfig)

    # Security gate levels
    gates: GateConfig = field(default_factory=GateConfig)

    # File filtering
    exclude_dirs: set[str] = field(default_factory=lambda: set(DEFAULT_EXCLUDE_DIRS))
    exclude_files: set[str] = field(default_factory=lambda: set(DEFAULT_EXCLUDE_FILES))
    allowed_extensions: set[str] = field(default_factory=lambda: set(DEFAULT_ALLOWED_EXTENSIONS))
    special_files: set[str] = field(default_factory=lambda: set(DEFAULT_SPECIAL_FILES))

    # Redaction
    enable_redaction: bool = True

    # Scanners to run automatically
    enabled_scanners: list[str] = field(default_factory=lambda: [
        "trivy", "bandit", "semgrep", "gitleaks",
    ])

    @property
    def max_file_size_bytes(self) -> int:
        """Convert KB limit to bytes."""
        return self.limits.max_file_size_kb * 1024

    @property
    def output_dir(self) -> str:
        return self.output.directory


# ─── Loader ────────────────────────────────────────────────────────────────────

def load_config(project_root: Path | None = None) -> VAFConfig:
    """
    Load VAF configuration from vaf.config.yaml if it exists.
    Falls back to defaults if file is missing or YAML is not available.

    Args:
        project_root: Root directory to search for vaf.config.yaml.
                      Defaults to current working directory.

    Returns:
        VAFConfig instance with merged settings.
    """
    config = VAFConfig()

    if project_root is None:
        project_root = Path(os.getcwd())

    config_path = project_root / "vaf.config.yaml"
    if not config_path.exists():
        return config

    if not _YAML_AVAILABLE:
        import warnings
        warnings.warn(
            "pyyaml not installed — vaf.config.yaml ignored. "
            "Install with: pip install pyyaml",
            stacklevel=2,
        )
        return config

    try:
        raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        import warnings
        warnings.warn(f"Failed to parse vaf.config.yaml: {exc}", stacklevel=2)
        return config

    # Apply top-level overrides
    if "language" in raw:
        config.language = str(raw["language"])
    if "mode" in raw:
        config.mode = str(raw["mode"])
    if "enable_redaction" in raw:
        config.enable_redaction = bool(raw["enable_redaction"])

    # Limits
    if limits := raw.get("limits"):
        if "max_total_files" in limits:
            config.limits.max_total_files = int(limits["max_total_files"])
        if "max_file_size_kb" in limits:
            config.limits.max_file_size_kb = int(limits["max_file_size_kb"])
        if "max_total_tokens" in limits:
            config.limits.max_total_tokens = int(limits["max_total_tokens"])

    # Output
    if output := raw.get("output"):
        if "formats" in output:
            config.output.formats = list(output["formats"])
        if "directory" in output:
            config.output.directory = str(output["directory"])

    # Standards
    if standards := raw.get("standards"):
        if "web" in standards:
            config.standards.web = list(standards["web"])
        if "ai" in standards:
            config.standards.ai = list(standards["ai"])
        if "supply_chain" in standards:
            config.standards.supply_chain = list(standards["supply_chain"])
        if "privacy" in standards:
            config.standards.privacy = list(standards["privacy"])

    # Exclude dirs — merge with defaults
    if exclude := raw.get("exclude"):
        if dirs := exclude.get("dirs"):
            config.exclude_dirs = config.exclude_dirs | set(dirs)
        if files := exclude.get("files"):
            config.exclude_files = config.exclude_files | set(files)

    # Include extensions — override defaults if specified
    if include := raw.get("include"):
        if exts := include.get("extensions"):
            config.allowed_extensions = set(exts)

    # Scanners
    if "enabled_scanners" in raw:
        config.enabled_scanners = list(raw["enabled_scanners"])

    # Gates
    if gates := raw.get("gates"):
        if "local" in gates:
            config.gates.local = str(gates["local"])
        if "pr" in gates:
            config.gates.pr = str(gates["pr"])
        if "staging" in gates:
            config.gates.staging = str(gates["staging"])
        if "production" in gates:
            config.gates.production = str(gates["production"])

    return config
