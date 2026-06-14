"""
VAF Scanners Package — Automatic security tool runners.

Each scanner module implements:
- is_available() -> bool
- run(path, config) -> ScanResult
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vaf.config import VAFConfig
from vaf.scanners import bandit, gitleaks, semgrep, trivy

_SCANNER_REGISTRY: dict[str, Any] = {
    "trivy": trivy,
    "bandit": bandit,
    "semgrep": semgrep,
    "gitleaks": gitleaks,
}


def run_scanners(
    root_dir: Path,
    tools: list[str],
    config: VAFConfig,
) -> dict[str, dict[str, Any]]:
    """
    Run requested scanners and return normalized results.

    Args:
        root_dir: Project root to scan.
        tools: List of scanner names to run.
        config: VAF configuration.

    Returns:
        Dict mapping tool name to result dict with keys:
        - status: "executed" | "skipped" | "error" | "not_installed"
        - findings: list of finding dicts
        - raw_output_path: path to raw output file
        - error_message: optional error string
    """
    results: dict[str, dict[str, Any]] = {}

    for tool in tools:
        if tool not in _SCANNER_REGISTRY:
            results[tool] = {
                "tool": tool,
                "status": "skipped",
                "findings": [],
                "raw_output_path": None,
                "error_message": f"Scanner '{tool}' not registered. Available: {list(_SCANNER_REGISTRY)}",
            }
            continue

        scanner = _SCANNER_REGISTRY[tool]
        if not scanner.is_available():
            results[tool] = {
                "tool": tool,
                "status": "not_installed",
                "findings": [],
                "raw_output_path": None,
                "error_message": f"Tool '{tool}' is not installed or not in PATH.",
            }
            continue

        try:
            result = scanner.run(root_dir, config)
            results[tool] = result
        except Exception as exc:
            results[tool] = {
                "tool": tool,
                "status": "error",
                "findings": [],
                "raw_output_path": None,
                "error_message": str(exc),
            }

    return results


__all__ = ["_SCANNER_REGISTRY", "run_scanners"]
