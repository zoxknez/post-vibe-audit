"""
VAF Evidence Module

Generates a tamper-evident index of all files included in the context bundle.
Each file gets a SHA-256 hash and a line inventory, so audit findings can be
verified against the actual files that were analyzed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FileEvidence:
    """Evidence record for a single file."""

    path: str
    sha256: str
    size_bytes: int
    line_count: int
    # Sampled line ranges for quick reference (key lines only)
    key_lines: dict[str, str] = field(default_factory=dict)


@dataclass
class EvidenceIndex:
    """Complete evidence index for a context bundle."""

    bundle_sha256: str = ""
    total_files: int = 0
    files: list[FileEvidence] = field(default_factory=list)
    _path_index: dict[str, FileEvidence] = field(default_factory=dict, repr=False)

    def add_file(self, evidence: FileEvidence) -> None:
        self.files.append(evidence)
        self._path_index[evidence.path] = evidence
        self.total_files = len(self.files)

    def get_file(self, path: str) -> FileEvidence | None:
        return self._path_index.get(path)

    def verify_file(self, path: str, current_content: str) -> bool:
        """Verify that a file's current content matches the recorded hash."""
        ev = self.get_file(path)
        if ev is None:
            return False
        current_hash = hashlib.sha256(current_content.encode("utf-8", errors="ignore")).hexdigest()
        return ev.sha256 == current_hash

    def as_dict(self) -> dict[str, Any]:
        return {
            "bundle_sha256": self.bundle_sha256,
            "total_files": self.total_files,
            "files": [
                {
                    "path": f.path,
                    "sha256": f.sha256,
                    "size_bytes": f.size_bytes,
                    "line_count": f.line_count,
                    "key_lines": f.key_lines,
                }
                for f in self.files
            ],
        }


def build_file_evidence(
    file_path: Path,
    content: str,
    rel_path: str,
) -> FileEvidence:
    """
    Build an evidence record for a single file.

    Args:
        file_path: Absolute path to the file.
        content: File content (may already be redacted).
        rel_path: Relative path string for display.

    Returns:
        FileEvidence with hash, size, and line inventory.
    """
    sha256 = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
    lines = content.splitlines()
    size = file_path.stat().st_size if file_path.exists() else len(content.encode("utf-8"))

    # Sample key lines: first 3, last 3, and any lines with "def ", "class ", "function ", "export"
    key_lines: dict[str, str] = {}
    important_keywords = ("def ", "class ", "function ", "export ", "async def ", "interface ", "type ")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(kw) for kw in important_keywords):
            key_lines[str(i)] = stripped[:120]  # truncate long lines
        if i <= 3 or i >= len(lines) - 2:
            key_lines[str(i)] = stripped[:120]

    return FileEvidence(
        path=rel_path,
        sha256=sha256,
        size_bytes=size,
        line_count=len(lines),
        key_lines=key_lines,
    )


def compute_bundle_hash(evidence_index: EvidenceIndex) -> str:
    """
    Compute a deterministic hash over all file hashes in the index.
    This acts as a tamper-evident seal for the entire bundle.
    """
    combined = "|".join(
        f"{f.path}:{f.sha256}" for f in sorted(evidence_index.files, key=lambda x: x.path)
    )
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def save_evidence_index(index: EvidenceIndex, output_path: Path) -> None:
    """
    Finalize and save evidence index to JSON.

    Args:
        index: EvidenceIndex to serialize.
        output_path: Path to write evidence_index.json.
    """
    index.bundle_sha256 = compute_bundle_hash(index)
    output_path.write_text(
        json.dumps(index.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
