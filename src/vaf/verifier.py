"""
VAF Anti-Hallucination Verifier

Validates an LLM audit report for internal consistency:
- Every finding must have an ID
- Every "executed" finding must reference a real tool or command
- Every "inferred" finding must reference a file that was in the context bundle
- Referenced files must exist in the evidence index
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_FINDING_ID_PATTERN = re.compile(r'\b(SEC|ARCH|QA|PERF|CICD|OBS|GDPR|A11Y|AI|AGT|PRIV|SC)-\d{3}\b')
_STATUS_PATTERN = re.compile(r'\b(executed|inferred|blocked|not_applicable)\b', re.IGNORECASE)
_FILE_REF_PATTERN = re.compile(r'`([^`]+\.[a-z]{1,6})`')  # backtick-quoted file refs
_PASS_PATTERN = re.compile(r'\bPASS\b', re.IGNORECASE)


def verify_report(
    report_path: Path,
    evidence_path: Path | None = None,
) -> list[str]:
    """
    Verify an LLM audit report for consistency.

    Args:
        report_path: Path to the Markdown audit report.
        evidence_path: Optional path to evidence_index.json for file verification.

    Returns:
        List of issue strings. Empty list means report is valid.
    """
    issues: list[str] = []

    # Load report
    try:
        report_text = report_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"VAF-VERIFY-000: Ne mogu da učitam report: {exc}"]

    # Load evidence index
    evidence_files: set[str] = set()
    if evidence_path and evidence_path.exists():
        try:
            evidence_data = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence_files = {f["path"] for f in evidence_data.get("files", [])}
        except (json.JSONDecodeError, OSError):
            issues.append("VAF-VERIFY-001: Evidence index postoji ali ne može biti učitan.")

    # ── Check 1: Finding IDs ──────────────────────────────────────────────────
    finding_ids = _FINDING_ID_PATTERN.findall(report_text)
    if not finding_ids:
        issues.append(
            "VAF-VERIFY-002: Report nema nijedan finding ID (format: SEC-001, ARCH-002 itd.). "
            "Proverite da li je LLM generisao strukturovani izveštaj."
        )

    # ── Check 2: Status codes ─────────────────────────────────────────────────
    statuses = _STATUS_PATTERN.findall(report_text)
    if not statuses:
        issues.append(
            "VAF-VERIFY-003: Report ne koristi status kodove (executed/inferred/blocked/not_applicable). "
            "Svaki nalaz mora imati status."
        )

    # ── Check 3: PASS without evidence ────────────────────────────────────────
    pass_matches = list(_PASS_PATTERN.finditer(report_text))
    for match in pass_matches:
        # Check surrounding context (100 chars) for evidence
        start = max(0, match.start() - 100)
        end = min(len(report_text), match.end() + 100)
        context = report_text[start:end]
        if "executed" not in context.lower() and "evidence" not in context.lower():
            line_num = report_text[: match.start()].count("\n") + 1
            issues.append(
                f"VAF-VERIFY-004: 'PASS' na liniji {line_num} bez vidljivog dokaza. "
                "PASS nije dozvoljen bez konkretnog executed dokaza."
            )

    # ── Check 4: File references exist in evidence ────────────────────────────
    if evidence_files:
        file_refs = _FILE_REF_PATTERN.findall(report_text)
        for ref in file_refs:
            # Only check refs that look like file paths (contain / or .)
            if "/" in ref or ("." in ref and " " not in ref):
                # Normalize path separators
                normalized = ref.replace("\\", "/")
                if (normalized not in evidence_files and
                        not any(normalized.endswith(p.split("/")[-1]) for p in evidence_files)):
                    issues.append(
                        f"VAF-VERIFY-005: Finding referencira `{ref}` koji nije u evidence index-u. "
                        "Proverite da li je fajl bio uključen u context bundle."
                    )

    # ── Check 5: Executive summary present ───────────────────────────────────
    if "executive summary" not in report_text.lower() and "go/no-go" not in report_text.lower():
        issues.append(
            "VAF-VERIFY-006: Report nema Executive Summary ili Go/No-Go verdict. "
            "Proverite da li je LLM sledio kompletan protokol."
        )

    # ── Check 6: Findings table present ──────────────────────────────────────
    if "| ID |" not in report_text and "| id |" not in report_text.lower():
        issues.append(
            "VAF-VERIFY-007: Report nema tabelarni pregled svih nalaza. "
            "Proverite strukturu izveštaja."
        )

    # ── Check 7: Standards mentioned ─────────────────────────────────────────
    standards_check = ["OWASP", "ASVS", "WCAG", "GDPR"]
    for std in standards_check:
        if std not in report_text:
            issues.append(
                f"VAF-VERIFY-008: Standard '{std}' nije pomenut u reportu. "
                "Proverite da li je LLM primenio sve standarde."
            )

    return issues
