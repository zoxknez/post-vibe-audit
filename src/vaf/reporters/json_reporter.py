"""
VAF JSON Reporter

Generates structured findings.json with standardized schema.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vaf import __version__


def generate(input_dir: Path, output_dir: Path) -> Path | None:
    """
    Generate findings.json from scan results.

    The output schema:
    {
      "vaf_version": "3.0.0",
      "generated_at": "...",
      "project": {...},
      "summary": {"critical": 0, "high": 0, ...},
      "findings": [...]
    }
    """
    scans_dir = input_dir / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "findings.json"

    all_findings: list[dict[str, Any]] = []
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    # Collect from all scanner outputs
    if scans_dir.exists():
        for scan_file in sorted(scans_dir.glob("*.json")):
            try:
                data = json.loads(scan_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    findings = data.get("findings", [])
                    tool_name = scan_file.stem
                    for f in findings:
                        severity = f.get("severity", "info").lower()
                        if severity in summary:
                            summary[severity] += 1
                        all_findings.append({
                            "source_tool": tool_name,
                            **f,
                        })
            except (json.JSONDecodeError, OSError):
                continue

    report = {
        "vaf_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0",
        "project": {
            "scan_path": str(input_dir.parent) if input_dir.name == ".vibe_audit" else str(input_dir),
        },
        "summary": summary,
        "total_findings": len(all_findings),
        "findings": all_findings,
    }

    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path
