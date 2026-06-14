"""
VAF Reporters Package
"""

from __future__ import annotations

from pathlib import Path

from vaf.reporters import json_reporter, markdown_reporter, sarif_reporter


def generate_reports(input_dir: Path, output_dir: Path, formats: list[str]) -> list[Path]:
    """
    Generate reports in requested formats from scan results in input_dir.

    Args:
        input_dir: Directory containing .vibe_audit/ scan outputs.
        output_dir: Where to write generated reports.
        formats: List of format strings: markdown, json, sarif.

    Returns:
        List of generated file paths.
    """
    generated: list[Path] = []

    for fmt in formats:
        fmt = fmt.strip().lower()
        if fmt in ("json",):
            path = json_reporter.generate(input_dir, output_dir)
            if path:
                generated.append(path)
        elif fmt in ("sarif",):
            path = sarif_reporter.generate(input_dir, output_dir)
            if path:
                generated.append(path)
        elif fmt in ("markdown", "md"):
            path = markdown_reporter.generate(input_dir, output_dir)
            if path:
                generated.append(path)

    return generated
