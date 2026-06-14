"""
VAF Packer — Context Bundle Generator

Collects repository context into a single LLM-ready Markdown file.
Replaces the legacy scripts/vibe_audit_packer.py with a config-driven,
redaction-aware, evidence-indexed implementation.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from vaf.config import VAFConfig, load_config
from vaf.evidence import EvidenceIndex, build_file_evidence, save_evidence_index
from vaf.redaction import RedactionReport, redact_content, save_secrets_report

# ─── Packing strategies ────────────────────────────────────────────────────────

# File importance scoring — higher = more important
_IMPORTANCE: dict[str, int] = {
    "auth": 100,
    "login": 95,
    "session": 90,
    "token": 88,
    "oauth": 88,
    "jwt": 85,
    "permission": 85,
    "middleware": 80,
    "api": 75,
    "route": 75,
    "handler": 70,
    "schema": 68,
    "migration": 65,
    "model": 62,
    "config": 60,
    "env": 58,
    "secret": 55,
    "test": 40,
    "spec": 38,
    "mock": 30,
    "style": 20,
    "css": 18,
    "component": 50,
    "service": 65,
    "repository": 62,
    "controller": 68,
}

# Security-focused file patterns for security-first strategy
_SECURITY_PATTERNS = {
    "auth", "login", "logout", "session", "token", "jwt", "oauth",
    "permission", "role", "middleware", "guard", "policy", "crypto",
    "password", "credential", "secret", "key", "cert", "ssl", "tls",
}


def _file_importance_score(rel_path: str) -> int:
    """Score a file by importance for audit context."""
    parts = rel_path.lower().replace("\\", "/").split("/")
    name = parts[-1] if parts else rel_path.lower()
    score = 0
    for segment in [*parts, name]:
        for keyword, weight in _IMPORTANCE.items():
            if keyword in segment:
                score = max(score, weight)

    # Cap test/spec/mock files so they don't override core logic files
    is_test = any(kw in rel_path.lower() for kw in ["test", "spec", "mock"])
    if is_test:
        score = min(score, 45)
    return score


def _is_security_relevant(rel_path: str) -> bool:
    """Check if file is relevant for security-first strategy."""
    lower = rel_path.lower()
    return any(pat in lower for pat in _SECURITY_PATTERNS)


# ─── Git helpers ───────────────────────────────────────────────────────────────

def _run_cmd(args: list[str], cwd: str, timeout: int = 30) -> str:
    """Run a shell command and return stdout, empty string on error."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
            timeout=timeout,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def get_git_info(root_dir: str) -> dict[str, str]:
    """Collect git repository metadata."""
    info: dict[str, str] = {}
    info["branch"] = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], root_dir)
    info["commit_sha"] = _run_cmd(["git", "rev-parse", "HEAD"], root_dir)
    info["commit_short"] = _run_cmd(["git", "rev-parse", "--short", "HEAD"], root_dir)
    info["remote_url"] = _run_cmd(["git", "remote", "get-url", "origin"], root_dir)
    info["status"] = _run_cmd(["git", "status", "-s"], root_dir)
    info["diff"] = _run_cmd(["git", "diff", "HEAD"], root_dir)
    if not info["diff"]:
        info["diff"] = _run_cmd(["git", "diff"], root_dir)
    info["log_recent"] = _run_cmd(
        ["git", "log", "--oneline", "-10", "--no-walk", "HEAD"], root_dir
    )
    return info


def get_changed_files(root_dir: str, base: str = "HEAD") -> list[str]:
    """Return list of files changed relative to base."""
    output = _run_cmd(["git", "diff", "--name-only", base], root_dir)
    if not output:
        output = _run_cmd(["git", "diff", "--name-only", "--cached"], root_dir)
    return [f.strip() for f in output.splitlines() if f.strip()]


# ─── Stack detection ───────────────────────────────────────────────────────────

def detect_stack(root_dir: Path) -> dict[str, object]:
    """Detect the project technology stack from manifest files."""
    stack: dict[str, object] = {
        "has_python": False,
        "has_nodejs": False,
        "has_java": False,
        "has_go": False,
        "has_rust": False,
        "has_dotnet": False,
        "has_docker": False,
        "has_k8s": False,
        "has_terraform": False,
        "has_github_actions": False,
        "has_gitlab_ci": False,
        "has_nextjs": False,
        "has_prisma": False,
        "has_fastapi": False,
        "has_django": False,
        "has_llm_usage": False,
        "package_managers": [],
    }

    checks: dict[str, list[str]] = {
        "has_python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
        "has_nodejs": ["package.json"],
        "has_java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "has_go": ["go.mod"],
        "has_rust": ["Cargo.toml"],
        "has_docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "has_terraform": ["*.tf"],
    }

    for flag, files in checks.items():
        for file_pattern in files:
            if "*" in file_pattern:
                if list(root_dir.glob(f"**/{file_pattern}")):
                    stack[flag] = True
            elif (root_dir / file_pattern).exists():
                stack[flag] = True

    stack["has_github_actions"] = (root_dir / ".github" / "workflows").exists()
    stack["has_gitlab_ci"] = (root_dir / ".gitlab-ci.yml").exists()
    stack["has_k8s"] = (root_dir / "k8s").exists() or (root_dir / "kubernetes").exists()
    stack["has_nextjs"] = (root_dir / "next.config.js").exists() or (root_dir / "next.config.ts").exists() or (root_dir / "next.config.mjs").exists()
    stack["has_prisma"] = (root_dir / "prisma").exists()

    # LLM usage detection
    llm_indicators = [
        "openai", "anthropic", "langchain", "llamaindex", "llama_index",
        "langsmith", "litellm", "groq", "together", "mistral", "gemini",
        "vertexai", "bedrock", "mcp", "autogen", "crewai",
    ]
    pkg_files = ["package.json", "requirements.txt", "pyproject.toml"]
    for pf in pkg_files:
        pf_path = root_dir / pf
        if pf_path.exists():
            content = pf_path.read_text(encoding="utf-8", errors="ignore").lower()
            if any(ind in content for ind in llm_indicators):
                stack["has_llm_usage"] = True

    # Package managers
    pms: list[str] = []
    for pm, lockfile in [("npm", "package-lock.json"), ("yarn", "yarn.lock"),
                          ("pnpm", "pnpm-lock.yaml"), ("poetry", "poetry.lock"),
                          ("uv", "uv.lock")]:
        if (root_dir / lockfile).exists():
            pms.append(pm)
    stack["package_managers"] = pms

    return stack


# ─── File tree ─────────────────────────────────────────────────────────────────

def generate_file_tree(root_dir: str, config: VAFConfig) -> str:
    """Generate a printable directory tree string."""
    lines: list[str] = []

    def _walk(directory: str, prefix: str = "") -> None:
        try:
            items = sorted(os.listdir(directory))
        except PermissionError:
            return

        filtered = []
        for item in items:
            path = os.path.join(directory, item)
            if os.path.isdir(path):
                if item not in config.exclude_dirs and not item.startswith(".vibe_audit"):
                    filtered.append(item)
            else:
                if item not in config.exclude_files:
                    _, ext = os.path.splitext(item)
                    if ext.lower() in config.allowed_extensions or item in config.special_files:
                        filtered.append(item)

        for i, item in enumerate(filtered):
            is_last = i == len(filtered) - 1
            connector = "└── " if is_last else "├── "
            path = os.path.join(directory, item)
            lines.append(f"{prefix}{connector}{item}")
            if os.path.isdir(path):
                new_prefix = prefix + ("    " if is_last else "│   ")
                _walk(path, new_prefix)

    lines.append(f"{os.path.basename(root_dir)}/")
    _walk(root_dir)
    return "\n".join(lines)


# ─── Dependency info ───────────────────────────────────────────────────────────

def collect_dependency_info(root_dir: Path, config: VAFConfig) -> str:
    """Collect dependency manifest files content."""
    sections: list[str] = []
    manifests = [
        "package.json", "pyproject.toml", "requirements.txt", "requirements-dev.txt",
        "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "uv.lock",
    ]
    for manifest in manifests:
        path = root_dir / manifest
        if path.exists() and path.stat().st_size < config.max_file_size_bytes:
            content = path.read_text(encoding="utf-8", errors="ignore")
            if config.enable_redaction:
                content = redact_content(content, str(path))
            sections.append(f'<dependency_manifest name="{manifest}">\n{content}\n</dependency_manifest>\n')
    return "\n".join(sections) if sections else "*Nema detektovanih manifest fajlova zavisnosti.*"


# ─── ADR collection ────────────────────────────────────────────────────────────

def collect_adrs(vibe_audit_dir: Path) -> str:
    """Collect Architecture Decision Records."""
    adrs_path = vibe_audit_dir / "adrs"
    if not adrs_path.exists():
        return "*Nema ADR-ova u .vibe_audit/adrs/ — preporučujemo dokumentovanje arhitektonskih odluka.*"

    adr_files = sorted(adrs_path.glob("*.md"))
    if not adr_files:
        return "*Nema ADR fajlova u .vibe_audit/adrs/ — preporučujemo dokumentovanje arhitektonskih odluka.*"

    sections: list[str] = []
    for adr_file in adr_files:
        try:
            content = adr_file.read_text(encoding="utf-8", errors="ignore")
            sections.append(f"### {adr_file.name}\n```markdown\n{content}\n```\n")
        except Exception as exc:
            sections.append(f"### {adr_file.name}\n*Greška pri čitanju: {exc}*\n")
    return "\n".join(sections)


# ─── Scope matrix ──────────────────────────────────────────────────────────────

def generate_scope_matrix(
    root_dir: Path,
    git_info: dict[str, str],
    stack: dict[str, object],
    config: VAFConfig,
) -> str:
    """Generate scope matrix of available artifacts."""

    def check(condition: object) -> str:
        return "[OK] available" if condition else "[-] unspecified"

    pm_list = stack.get("package_managers", [])
    pm_str = ", ".join(pm_list) if isinstance(pm_list, list) else "N/A"

    lines = ["## 2. Scope & Artefakt Matrica\n"]
    lines.append("| # | Kategorija artefakta | Status | Napomena |")
    lines.append("|---|---|---|---|")

    adrs_exist = list((root_dir / ".vibe_audit" / "adrs").glob("*.md")) if (root_dir / ".vibe_audit" / "adrs").exists() else []
    items = [
        ("Repo URL", check(git_info.get("remote_url")), git_info.get("remote_url", "N/A")),
        ("Branch", check(git_info.get("branch")), git_info.get("branch", "N/A")),
        ("Commit SHA", check(git_info.get("commit_sha")), git_info.get("commit_short", "N/A")),
        ("Aktivne Git izmene", check(git_info.get("status")),
         f"{len(git_info.get('status', '').splitlines())} izmenjenih fajlova" if git_info.get("status") else "čist radni direktorijum"),
        ("Python manifest", check(stack.get("has_python")), "pyproject.toml / requirements.txt"),
        ("Node.js manifest", check(stack.get("has_nodejs")), f"Package manager: {pm_str}"),
        ("Next.js projekt", check(stack.get("has_nextjs")), "next.config.* detektovan"),
        ("Prisma ORM", check(stack.get("has_prisma")), "prisma/ direktorijum"),
        ("Java manifest", check(stack.get("has_java")), "pom.xml / build.gradle"),
        ("Go manifest", check(stack.get("has_go")), "go.mod"),
        ("Rust manifest", check(stack.get("has_rust")), "Cargo.toml"),
        ("Dockerfile / docker-compose", check(stack.get("has_docker")), ""),
        ("Kubernetes manifesti", check(stack.get("has_k8s")), "k8s/ ili kubernetes/"),
        ("Terraform/IaC fajlovi", check(stack.get("has_terraform")), "*.tf"),
        ("GitHub Actions workflows", check(stack.get("has_github_actions")), ".github/workflows/"),
        ("GitLab CI/CD konfiguracija", check(stack.get("has_gitlab_ci")), ".gitlab-ci.yml"),
        ("LLM/AI library usage", check(stack.get("has_llm_usage")), "openai/anthropic/langchain/mcp u dependencies"),
        ("ADR-ovi", check(adrs_exist), f"{len(adrs_exist)} ADR fajlova" if adrs_exist else ""),
        ("Runtime logovi", "⚠️ unspecified", "Nije dostavljeno — označiti kao `blocked` gdje relevantno"),
        ("Metrike i tracing", "⚠️ unspecified", "Nije dostavljeno — označiti kao `blocked` gdje relevantno"),
        ("Load/stress test rezultati", "⚠️ unspecified", "Nije dostavljeno"),
        ("OpenAPI/GraphQL specifikacija", "⚠️ unspecified", "Nije dostavljeno — API analiza limitirana"),
        ("Env inventar (redaktovan)", "⚠️ unspecified", "Nikad ne dostavljaj sirove tajne"),
        ("SBOM", "⚠️ unspecified", "sbom.json / cyclonedx.json nije pronađen"),
        ("SLSA provenance", "⚠️ unspecified", "Attestation nije pronađena"),
        ("AI context window protection", check(config.enable_redaction), "vaf redakcija tajni"),
    ]

    for i, (name, status, note) in enumerate(items, 1):
        lines.append(f"| {i} | {name} | {status} | {note} |")

    lines.append("")
    lines.append("> **Napomena**: Artefakti označeni kao `unspecified` uzrokuju status `blocked` u odgovarajućim nalazima.")
    lines.append("")
    return "\n".join(lines)


# ─── Recommended commands ──────────────────────────────────────────────────────

def generate_recommended_commands(stack: dict[str, object]) -> str:
    """Generate recommended scan commands based on detected stack."""
    lines = ["## Preporučene Komande za Proveru (prilagoditi steku)\n"]
    lines.append("> Pokrenite ove komande u projektu koji analizirate i priložite izlaze:\n")

    if stack.get("has_python"):
        lines += [
            "```bash",
            "# Python — Bandit AST bezbednosna analiza",
            "bandit -r . -f json -o bandit.json --exit-zero",
            "",
            "# Python — Testovi i coverage",
            "pytest -q --junit-xml=pytest.xml \\",
            "       --cov=. --cov-report=xml:coverage.xml \\",
            "       --cov-report=html:coverage-html \\",
            "       --cov-report=json:coverage.json",
            "```\n",
        ]

    if stack.get("has_nodejs"):
        lines += [
            "```bash",
            "# Node.js — ESLint statička analiza",
            "npx eslint . --format json --output-file eslint-results.json",
            "```\n",
        ]

    if stack.get("has_java"):
        lines += [
            "```bash",
            "# Java — Testovi i JaCoCo coverage",
            "mvn test jacoco:report && mvn verify",
            "```\n",
        ]

    lines += [
        "```bash",
        "# Zavisnosti / tajne / misconfiguracija (Trivy)",
        "trivy fs --scanners vuln,misconfig,secret,license . \\",
        "         --format json --output trivy-fs.json",
        "",
        "# Semgrep SAST (multi-language)",
        "semgrep --config=auto . --json --output semgrep.json",
        "",
        "# Gitleaks — git istorija secrets scan",
        "gitleaks detect --source . --report-format json --report-path gitleaks.json",
        "",
        "# OpenSSF Scorecard (supply chain)",
        "scorecard --repo=<github.com/org/repo> --format json",
        "```\n",
    ]

    if stack.get("has_docker"):
        lines += [
            "```bash",
            "# Docker image scan",
            "trivy image <image-ref> --format json --output trivy-image.json",
            "",
            "# SBOM generisanje (CycloneDX format)",
            "trivy image <image-ref> --format cyclonedx --output sbom.json",
            "```\n",
        ]

    lines += [
        "```bash",
        "# DAST — web aplikacija (OWASP ZAP) — samo na test okruženju!",
        "docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \\",
        "  -t <target-url> -r zap-baseline.html",
        "",
        "# Accessibility (Lighthouse CLI + axe)",
        "npx lighthouse <url> \\",
        "  --output=json,html --output-path=./lighthouse-report \\",
        "  --only-categories=accessibility,performance,best-practices \\",
        "  --chrome-flags='--headless'",
        "```\n",
    ]

    if stack.get("has_llm_usage"):
        lines += [
            "```bash",
            "# AI/LLM specifični audit",
            "# Proverite: da li postoji prompt injection zaštita?",
            "# Proverite: da li se korisnički input sanitizuje pre slanja LLM-u?",
            "# Proverite: da li su tool pozivi na allowlist-u?",
            "# Proverite: da li destruktivne akcije zahtevaju human approval?",
            "# Alat: Garak (LLM vulnerability scanner)",
            "# pip install garak && garak --model openai --probes all",
            "```\n",
        ]

    return "\n".join(lines)


# ─── File collection ───────────────────────────────────────────────────────────

def collect_file_contents(
    root_dir: Path,
    config: VAFConfig,
    strategy: str = "deep",
    changed_files: list[str] | None = None,
    redaction_report: RedactionReport | None = None,
) -> tuple[list[str], list[str], EvidenceIndex]:
    """
    Collect file contents based on strategy.

    Args:
        root_dir: Project root directory.
        config: VAF configuration.
        strategy: One of: deep, quick, security-first, changed-files, architecture.
        changed_files: List of changed files (for changed-files strategy).
        redaction_report: Optional report to accumulate redaction findings.

    Returns:
        Tuple of (content_blocks, skipped_files, evidence_index)
    """
    contents: list[str] = []
    skipped: list[str] = []
    evidence = EvidenceIndex()
    if redaction_report is None and config.enable_redaction:
        redaction_report = RedactionReport()

    # Gather all candidate files with scores
    candidates: list[tuple[int, Path, str]] = []  # (score, path, rel_path)

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in sorted(dirs) if d not in config.exclude_dirs]

        for file in sorted(files):
            if file in config.exclude_files:
                continue

            file_path = Path(root) / file
            try:
                rel_path = file_path.relative_to(root_dir).as_posix()
            except ValueError:
                continue
            _, ext = os.path.splitext(file)

            if ext.lower() not in config.allowed_extensions and file not in config.special_files:
                continue

            # Strategy filtering
            if strategy == "changed-files":
                if changed_files is not None and rel_path not in changed_files:
                    # Still include security-critical files regardless
                    if not _is_security_relevant(rel_path):
                        continue
            elif strategy == "security-first":
                if not _is_security_relevant(rel_path) and file not in config.special_files:
                    continue
            elif strategy == "architecture":
                arch_keywords = {"readme", "readme.md", "package.json", "pyproject.toml",
                                 "requirements.txt", "go.mod", "cargo.toml"}
                arch_dirs = {"docs", "src", "lib", "types", "interfaces", "services"}
                if (file.lower() not in arch_keywords and
                        not any(d in rel_path.lower() for d in arch_dirs)):
                    # Only top-level files and known architecture files
                    if rel_path.count("/") > 2:
                        continue

            score = _file_importance_score(rel_path)
            candidates.append((score, file_path, rel_path))

    # Sort by importance score (descending) for smart inclusion
    candidates.sort(key=lambda x: -x[0])

    # Apply strategy-specific quick mode limits
    if strategy == "quick":
        max_files = min(config.limits.max_total_files, 80)
    else:
        max_files = config.limits.max_total_files

    for score, file_path, rel_path in candidates:
        if len(contents) >= max_files:
            skipped.append(f"Dostignut limit od {max_files} fajlova — {rel_path} izostavljen.")
            continue

        try:
            size = file_path.stat().st_size
            if size > config.max_file_size_bytes:
                skipped.append(f"{rel_path} ({size / 1024:.0f} KB — prevelik, limit: {config.limits.max_file_size_kb} KB)")
                continue

            raw_content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Redact secrets before including
            if config.enable_redaction:
                if redaction_report is not None:
                    redaction_report.total_files_scanned += 1
                content = redact_content(raw_content, rel_path, redaction_report)
            else:
                content = raw_content

            # Build evidence record
            ev = build_file_evidence(file_path, content, rel_path)
            evidence.add_file(ev)

            _, ext = os.path.splitext(file_path.name)
            contents.append(
                f'<file path="{rel_path}" size="{size}" sha256="{ev.sha256}" '
                f'importance="{score}" extension="{ext.lower() or "none"}">\n'
                f'{content}\n'
                f'</file>\n'
            )
        except Exception as exc:
            skipped.append(f"{rel_path} (greška: {exc})")

    return contents, skipped, evidence


# ─── Prompt loader ─────────────────────────────────────────────────────────────

def load_pro_prompt(root_dir: Path) -> str:
    """Load Pro Audit Mega-Prompt from prompts/ directory."""
    prompt_path = root_dir / "prompts" / "pro_audit_prompt.md"
    if prompt_path.exists():
        content = prompt_path.read_text(encoding="utf-8", errors="ignore")
        if "---BEGIN PROMPT---" in content and "---END PROMPT---" in content:
            start = content.index("---BEGIN PROMPT---") + len("---BEGIN PROMPT---")
            end = content.index("---END PROMPT---")
            return content[start:end].strip()
        return content
    return ""


# ─── Main pack function ────────────────────────────────────────────────────────

def pack(
    root_dir: Path,
    mode: str = "deep",
    strategy: str | None = None,
    config: VAFConfig | None = None,
    verbose: bool = True,
) -> Path:
    """
    Pack project context into a single LLM-ready Markdown bundle.

    Args:
        root_dir: Project root directory to analyze.
        mode: Analysis mode (deep or quick).
        strategy: Packing strategy. Defaults to mode-appropriate strategy.
        config: VAF configuration. Loaded from vaf.config.yaml if None.
        verbose: Print progress to stdout.

    Returns:
        Path to the generated CURRENT_CONTEXT.md file.
    """
    if config is None:
        config = load_config(root_dir)

    if strategy is None:
        strategy = "quick" if mode == "quick" else "deep"

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    log("[VAF] =================================================")
    log("[VAF]  Vibe-Audit Framework v3.0 - Context Packer")
    log("[VAF] =================================================")
    log(f"[VAF] Root direktorijum : {root_dir}")
    log(f"[VAF] Režim analize     : {mode}")
    log(f"[VAF] Strategija        : {strategy}")
    log(f"[VAF] Redakcija tajni   : {'uključena' if config.enable_redaction else 'isključena'}")
    log(f"[VAF] Vreme             : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("[VAF] -------------------------------------------------")

    # Prepare output directories
    vibe_audit_dir = root_dir / ".vibe_audit"
    vibe_audit_dir.mkdir(exist_ok=True)
    (vibe_audit_dir / "adrs").mkdir(exist_ok=True)
    (vibe_audit_dir / "scans").mkdir(exist_ok=True)
    output_file = vibe_audit_dir / "CURRENT_CONTEXT.md"

    # Collect data
    log("[VAF] [1/6] Prikupljanje Git informacija...")
    git_info = get_git_info(str(root_dir))

    log("[VAF] [2/6] Detekcija tehnološkog steka...")
    stack = detect_stack(root_dir)
    detected = [k.replace("has_", "") for k, v in stack.items() if v and k.startswith("has_")]
    log(f"[VAF]       Detektovano: {', '.join(detected) or 'ništa specifično'}")

    log("[VAF] [3/6] Generisanje stabla direktorijuma...")
    file_tree = generate_file_tree(str(root_dir), config)

    log("[VAF] [4/6] Prikupljanje informacija o zavisnostima...")
    dependency_info = collect_dependency_info(root_dir, config)

    log("[VAF] [5/6] Prikupljanje ADR-ova...")
    adrs_content = collect_adrs(vibe_audit_dir)

    log("[VAF] [6/6] Prikupljanje sadržaja fajlova...")
    changed_files: list[str] | None = None
    if strategy == "changed-files":
        changed_files = get_changed_files(str(root_dir))
    redaction_report = RedactionReport() if config.enable_redaction else None
    file_contents, skipped_files, evidence_index = collect_file_contents(
        root_dir, config, strategy=strategy, changed_files=changed_files, redaction_report=redaction_report
    )
    log(f"[VAF]       Uključeno fajlova: {len(file_contents)}, Preskočeno: {len(skipped_files)}")

    # Save evidence index
    evidence_path = vibe_audit_dir / "evidence_index.json"
    save_evidence_index(evidence_index, evidence_path)
    log(f"[VAF]       Evidence index sačuvan: {evidence_path}")

    # Save secrets report
    if redaction_report:
        secrets_report_path = vibe_audit_dir / "secrets_report.json"
        save_secrets_report(redaction_report, secrets_report_path)
        log(f"[VAF]       Secrets report sačuvan: {secrets_report_path}")

    # Generate auxiliary sections
    scope_matrix = generate_scope_matrix(root_dir, git_info, stack, config)
    recommended_commands = generate_recommended_commands(stack)

    # Load prompt
    mega_prompt = load_pro_prompt(root_dir)
    if (root_dir / "prompts" / "pro_audit_prompt.md").exists():
        log("[VAF]       Pro Mega-Prompt učitan iz prompts/pro_audit_prompt.md")
    else:
        log("[VAF]       ⚠️ prompts/pro_audit_prompt.md nije pronađen — dodajte prompt za puni protokol")

    # Compile output
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode_label = "BRZA PROVERA (1-2h)" if mode == "quick" else "DUBINSKA ANALIZA (1-3 dana)"

    log("[VAF] Kompajliranje kontekst paketa...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<!-- VAF v3.0 CURRENT_CONTEXT.md — Auto-generated, DO NOT EDIT -->\n\n")
        f.write("# AUDIT PROTOKOL I SISTEMSKE INSTRUKCIJE\n")
        f.write(f"> Generisano: **{timestamp}** | Režim: **{mode_label}** | "
                f"Strategija: **{strategy}** | Target: `{root_dir}`\n\n")
        f.write("Primenite ovaj protokol na kontekst repozitorijuma u nastavku:\n\n")

        if mega_prompt:
            f.write(mega_prompt)
            f.write("\n\n---\n\n")

        f.write("# STANJE REPOZITORIJUMA I KONTEKST BUNDLE\n\n")
        f.write("## 1. Osnovna Identifikacija\n\n")
        f.write("| Polje | Vrednost |\n|---|---|\n")
        f.write(f"| **Bundle generisan** | {timestamp} |\n")
        f.write(f"| **Modo analize** | {mode_label} |\n")
        f.write(f"| **Strategija pakovanja** | {strategy} |\n")
        f.write(f"| **Target direktorijum** | `{root_dir}` |\n")
        f.write(f"| **Remote URL** | `{git_info.get('remote_url', 'unspecified')}` |\n")
        f.write(f"| **Branch** | `{git_info.get('branch', 'unspecified')}` |\n")
        f.write(f"| **Commit SHA** | `{git_info.get('commit_sha', 'unspecified')}` |\n")
        f.write(f"| **Detektovani stek** | {', '.join(detected) or 'unspecified'} |\n")
        f.write(f"| **Broj uključenih fajlova** | {len(file_contents)} |\n")
        f.write(f"| **Bundle SHA-256** | `{evidence_index.bundle_sha256[:16]}...` |\n")
        f.write(f"| **Redakcija tajni** | {'uključena ✅' if config.enable_redaction else 'isključena ⚠️'} |\n")
        f.write("| **Standardi** | OWASP Top 10:2025, OWASP ASVS 5.0, API Security:2023, LLM Top 10:2025, Agentic Top 10:2026 |\n")
        f.write("| **Accessibility** | WCAG 2.2 AA |\n")
        f.write("| **Privacy** | GDPR Čl.25/30/32 |\n\n")

        f.write(scope_matrix)

        f.write("## 3. Stablo direktorijuma\n\n```text\n")
        f.write(file_tree)
        f.write("\n```\n\n")

        f.write("## 4. Git Izmene (Vibe Coding Session)\n\n")
        if git_info.get("log_recent"):
            f.write("### Nedavni commit-ovi\n```text\n")
            f.write(git_info["log_recent"])
            f.write("\n```\n\n")
        if git_info.get("status"):
            f.write("### Aktivni status\n```text\n")
            f.write(git_info["status"])
            f.write("\n```\n\n")
        else:
            f.write("*Git status: čist radni direktorijum.*\n\n")
        if git_info.get("diff"):
            f.write("### Git Diff\n```diff\n")
            f.write(git_info["diff"][:50_000])  # cap diff size
            f.write("\n```\n\n")

        f.write("## 5. Manifest Fajlovi Zavisnosti\n\n")
        f.write(dependency_info)
        f.write("\n\n")

        f.write("## 6. Architecture Decision Records (ADR-ovi)\n\n")
        f.write(adrs_content)
        f.write("\n\n")

        f.write("## 7. Preporučene Komande za Proveru\n\n")
        f.write(recommended_commands)
        f.write("\n\n")

        if skipped_files:
            f.write("## 8. Preskočeni Fajlovi\n\n")
            f.write("*Sledeći fajlovi su preskočeni (preveliki, binarni ili van opsega):*\n\n")
            for sf in skipped_files:
                f.write(f"- {sf}\n")
            f.write("\n")

        sec_num = 9 if skipped_files else 8
        f.write(f"## {sec_num}. Kompletan Sadržaj Fajlova Baze Koda\n\n")
        f.write("*Svi relevantni fajlovi projekta za analizu. Svaki fajl ima SHA-256 hash za verifikaciju:*\n\n")
        for file_content in file_contents:
            f.write(file_content)

    file_size_kb = output_file.stat().st_size / 1024
    log("-------------------------------------------------")
    log("[VAF] USPEŠNO! Kontekst fajl generisan:")
    log(f"[VAF]   >> {output_file.absolute()}")
    log(f"[VAF]   >> Veličina: {file_size_kb:.1f} KB")
    log(f"[VAF]   >> Fajlova uključeno: {len(file_contents)}")
    log("[VAF] -------------------------------------------------")
    log("[VAF] SLEDEĆI KORAK:")
    log("[VAF]   Otvorite .vibe_audit/CURRENT_CONTEXT.md i prevucite")
    log("[VAF]   fajl u Claude, Gemini, ChatGPT ili bilo koji LLM.")
    log("[VAF]   AI će automatski primeniti višedimenzionalni audit protokol.")
    log("=================================================")

    return output_file
