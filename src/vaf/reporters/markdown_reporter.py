"""
VAF Markdown Reporter

Generates a human-readable scan summary report in Markdown format.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vaf import __version__


def generate(input_dir: Path, output_dir: Path) -> Path | None:
    """Generate scan_summary.md from scan results."""
    scans_dir = input_dir / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "scan_summary.md"

    tool_results: dict[str, dict[str, Any]] = {}
    if scans_dir.exists():
        for scan_file in sorted(scans_dir.glob("*.json")):
            try:
                data = json.loads(scan_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "findings" in data:
                    tool_results[scan_file.stem] = data
            except (json.JSONDecodeError, OSError):
                continue

    lines = [
        f"<!-- VAF v{__version__} — Scan Summary — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -->\n",
        "# VAF Scan Summary\n",
        f"> Generisano: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | VAF v{__version__}\n",
        "---\n",
    ]

    if not tool_results:
        lines.append("*Nema scan rezultata. Pokrenite `vaf scan` prvo.*\n")
    else:
        # Overview table
        lines.extend([
            "## Pregled Skenera\n",
            "| Alat | Status | Critical | High | Medium | Low | Ukupno |",
            "|---|---|---:|---:|---:|---:|---:|",
        ])
        grand_total = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for tool, result in sorted(tool_results.items()):
            findings = result.get("findings", [])
            counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for f in findings:
                sev = f.get("severity", "low").lower()
                if sev in counts:
                    counts[sev] += 1
                    grand_total[sev] += 1

            status_icon = "✅" if result.get("status") == "executed" else "⚠️"
            lines.append(
                f"| {tool} | {status_icon} {result.get('status', 'unknown')} "
                f"| {counts['critical']} | {counts['high']} | {counts['medium']} "
                f"| {counts['low']} | {len(findings)} |"
            )

        lines.extend([
            f"| **UKUPNO** | — | **{grand_total['critical']}** | **{grand_total['high']}** "
            f"| **{grand_total['medium']}** | **{grand_total['low']}** | **{sum(grand_total.values())}** |",
            "",
        ])

        # Go/No-Go based on findings
        if grand_total["critical"] > 0:
            verdict = "❌ NO-GO"
            reason = f"{grand_total['critical']} Critical nalaza — mora se rešiti pre produkcije."
        elif grand_total["high"] > 0:
            verdict = "⚠️ CONDITIONAL GO"
            reason = f"{grand_total['high']} High nalaza — preporučuje se rešavanje pre produkcije."
        else:
            verdict = "✅ GO"
            reason = "Nema Critical/High nalaza u automatskim skenovima."

        lines.extend([
            "## Automatski Verdict\n",
            f"**{verdict}** — {reason}\n",
            "> Napomena: Ovo je verdict automatskih skenova. LLM audit je neophodan za kompletan pregled.\n",
            "---\n",
        ])

        # Top findings per tool
        for tool, result in sorted(tool_results.items()):
            findings = result.get("findings", [])
            if not findings:
                continue

            # Show top 10 by severity
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            top_findings = sorted(
                findings,
                key=lambda f: severity_order.get(f.get("severity", "info").lower(), 4),
            )[:10]

            lines.extend([
                f"## {tool.capitalize()} — Top nalazi\n",
                "| ID | Severity | Fajl | Opis |",
                "|---|---|---|---|",
            ])
            for f in top_findings:
                file_info = f.get("file", "N/A")
                if len(file_info) > 50:
                    file_info = "..." + file_info[-47:]
                lines.append(
                    f"| {f.get('id', '—')} | {f.get('severity', '—').upper()} "
                    f"| {file_info} | {f.get('title', f.get('message', '—'))[:80]} |"
                )
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
