"""
VAF PR Review Mode

Analyzes a pull request diff to identify risk areas:
- Touched components (auth, payment, DB, etc.)
- Test coverage gaps
- Architecture concerns
- Missing test additions for changed areas
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from vaf.config import VAFConfig

# Risk areas — maps file patterns to risk information
_RISK_AREAS: list[tuple[list[str], str, str, str]] = [
    # (patterns, area_name, risk_level, reason)
    (["auth", "login", "logout", "session", "oauth", "jwt", "token"],
     "Authentication / Authorization", "CRITICAL",
     "Auth changes — posebno proveriti: session fixation, broken auth, privilege escalation"),
    (["payment", "stripe", "checkout", "invoice", "billing", "webhook"],
     "Payment Processing", "CRITICAL",
     "Payment handling — proveriti: idempotency, webhook signature, double-charge zaštitu"),
    (["prisma", "migration", "schema.prisma", "alembic", "flyway", "liquibase"],
     "Database Schema / Migration", "HIGH",
     "DB schema promenjena — proveriti: data integrity, backward compatibility, rollback plan"),
    (["middleware", "guard", "interceptor", "policy"],
     "Middleware / Request Pipeline", "HIGH",
     "Middleware promenjen — može uticati na sve endpointe"),
    (["admin", "backoffice", "internal"],
     "Admin / Internal APIs", "HIGH",
     "Admin funkcionalnost — proveriti: BFLA, privileged access kontrole"),
    (["api", "route", "handler", "controller", "endpoint"],
     "API Routes / Handlers", "MEDIUM",
     "API endpointi promenjeni — proveriti: autorizaciju, rate limiting, validaciju input-a"),
    (["config", "env", ".env.example", "settings"],
     "Configuration / Environment", "MEDIUM",
     "Konfiguracija promenjena — proveriti: novi env vars, sigurne vrednosti"),
    (["docker", "dockerfile", "compose", "k8s", "kubernetes", "helm"],
     "Infrastructure / Deployment", "MEDIUM",
     "Infrastruktura promenjena — proveriti: security kontekst, resource limits"),
    (["dependency", "package.json", "requirements.txt", "pyproject.toml", "cargo.toml", "go.mod"],
     "Dependencies", "MEDIUM",
     "Zavisnosti promenjene — pokrenuti Trivy/Snyk sken"),
    (["mcp", "agent", "llm", "openai", "anthropic", "langchain", "tool", "function_call"],
     "AI / Agent / LLM Integration", "HIGH",
     "AI/Agent kod promenjen — proveriti: prompt injection, tool permissions, human approval"),
]

_TEST_PATTERNS = ["test", "spec", "__tests__", ".test.", ".spec.", "cypress", "playwright", "e2e"]


def _run_git(args: list[str], cwd: str) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30,
            check=False,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _detect_risk_areas(changed_files: list[str]) -> list[dict[str, Any]]:
    """Identify which risk areas are touched by the changed files."""
    triggered: list[dict[str, Any]] = []
    seen_areas: set[str] = set()

    for file_path in changed_files:
        lower = file_path.lower()
        for patterns, area, risk, reason in _RISK_AREAS:
            if area in seen_areas:
                continue
            if any(pat in lower for pat in patterns):
                triggered.append({
                    "area": area,
                    "risk": risk,
                    "reason": reason,
                    "triggering_files": [f for f in changed_files
                                        if any(pat in f.lower() for pat in patterns)][:5],
                })
                seen_areas.add(area)

    # Sort by risk level
    risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    triggered.sort(key=lambda x: risk_order.get(x["risk"], 4))
    return triggered


def _detect_test_gaps(changed_files: list[str]) -> list[str]:
    """Find changed source files that don't have corresponding test changes."""
    source_files = [f for f in changed_files
                    if not any(pat in f.lower() for pat in _TEST_PATTERNS)]
    test_files_changed = [f for f in changed_files
                          if any(pat in f.lower() for pat in _TEST_PATTERNS)]

    gaps = []
    for src_file in source_files:
        # Check if any test file roughly corresponds to this source
        src_name = Path(src_file).stem.lower()
        has_test = any(src_name in t.lower() for t in test_files_changed)
        if not has_test:
            gaps.append(src_file)

    return gaps


def review_pr(
    root_dir: Path,
    base: str = "main",
    head: str = "HEAD",
    config: VAFConfig | None = None,
) -> str:
    """
    Generate a PR risk summary.

    Args:
        root_dir: Project root directory.
        base: Base branch/ref to compare against.
        head: Head branch/commit to analyze.
        config: VAF configuration.

    Returns:
        Markdown-formatted PR Risk Summary string.
    """
    cwd = str(root_dir)

    # Get changed files
    diff_output = _run_git(["diff", "--name-only", f"{base}...{head}"], cwd)
    if not diff_output:
        # Try staged files
        diff_output = _run_git(["diff", "--name-only", "--cached"], cwd)
    if not diff_output:
        # Fall back to all modified files
        diff_output = _run_git(["status", "--short"], cwd)
        # Parse git status format
        changed_files = [
            line[3:].strip() for line in diff_output.splitlines()
            if line.strip() and not line.startswith("??")
        ]
    else:
        changed_files = [f.strip() for f in diff_output.splitlines() if f.strip()]

    if not changed_files:
        return "## PR Risk Summary\n\n*Nema izmenjenih fajlova između `{base}` i `{head}`.*"

    # Analyze
    risk_areas = _detect_risk_areas(changed_files)
    test_gaps = _detect_test_gaps(changed_files)
    has_new_tests = any(any(pat in f.lower() for pat in _TEST_PATTERNS) for f in changed_files)

    # Build summary
    lines = [
        "## PR Risk Summary\n",
        f"> VAF PR Review | Base: `{base}` → Head: `{head}` | "
        f"Izmenjeno fajlova: **{len(changed_files)}**\n",
        "---\n",
        "### Izmenjeni fajlovi\n",
        "```",
    ]
    for f in changed_files[:30]:
        lines.append(f"  {f}")
    if len(changed_files) > 30:
        lines.append(f"  ... i još {len(changed_files) - 30} fajlova")
    lines.append("```\n")

    # Risk areas
    if risk_areas:
        lines.append("### Detektovane rizične oblasti\n")
        lines.append("| Oblast | Rizik | Razlog |")
        lines.append("|---|---|---|")
        for area in risk_areas:
            risk_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(area["risk"], "⚪")
            lines.append(f"| {area['area']} | {risk_icon} {area['risk']} | {area['reason']} |")
        lines.append("")
    else:
        lines.append("### Rizične oblasti\n\n✅ Nisu detektovane kritične rizične oblasti.\n")

    # Test gaps
    if test_gaps:
        lines.extend([
            "### Test Gap Upozorenja\n",
            "Sledeći fajlovi su izmenjeni bez odgovarajućih test promena:\n",
        ])
        for gap in test_gaps[:15]:
            lines.append(f"- ⚠️ `{gap}`")
        if len(test_gaps) > 15:
            lines.append(f"- ... i još {len(test_gaps) - 15} fajlova bez testova")
        lines.append("")
    elif has_new_tests:
        lines.append("### Testovi\n\n✅ PR uključuje izmene testova.\n")
    else:
        lines.append("### Testovi\n\n⚠️ PR ne uključuje izmene testova.\n")

    # Verdict
    critical_areas = [a for a in risk_areas if a["risk"] == "CRITICAL"]
    high_areas = [a for a in risk_areas if a["risk"] == "HIGH"]

    lines.append("---\n")
    if critical_areas and (test_gaps or not has_new_tests):
        verdict = "❌ NO-GO"
        verdict_reason = (
            f"CRITICAL rizične oblasti ({', '.join(a['area'] for a in critical_areas)}) "
            f"su promenjene bez adekvatnih testova."
        )
    elif critical_areas:
        verdict = "⚠️ CONDITIONAL GO"
        verdict_reason = (
            f"CRITICAL oblasti promenjene ({', '.join(a['area'] for a in critical_areas)}). "
            "Obavezna ručna provera pre merge-a."
        )
    elif high_areas and len(test_gaps) > len(changed_files) // 2:
        verdict = "⚠️ CONDITIONAL GO"
        verdict_reason = f"HIGH rizik + većina fajlova nema testove ({len(test_gaps)}/{len(changed_files)})."
    else:
        verdict = "✅ GO"
        verdict_reason = "Nema CRITICAL/HIGH rizika koji bi blokirao merge."

    lines.extend([
        "### Verdict\n",
        f"**{verdict}**\n",
        f"> {verdict_reason}\n",
        "",
        "---",
        "*Ovaj izveštaj je automatski. Za kompletan audit pokrenite: `vaf pack && vaf audit`*",
    ])

    return "\n".join(lines)
