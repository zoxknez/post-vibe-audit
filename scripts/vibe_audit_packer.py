#!/usr/bin/env python3
"""
DEPRECATED: Vibe-Audit Framework v2.0 Context Packer
=====================================================
Ova skripta je zadržana radi backwards compatibilnosti.
Od VAF v3.0, koristite CLI:

    pip install -e .
    vaf pack [--path /putanja] [--mode deep|quick]

Ova skripta poziva novi CLI i biće uklonjena u v4.0.
"""

import sys
import warnings

warnings.warn(
    "\n\n"
    "┌─────────────────────────────────────────────────────────────────┐\n"
    "│ DEPRECATED: scripts/vibe_audit_packer.py                       │\n"
    "│                                                                 │\n"
    "│ Od VAF v3.0, koristite novi CLI:                               │\n"
    "│                                                                 │\n"
    "│   pip install -e .                                             │\n"
    "│   vaf pack [--path .] [--mode deep|quick]                      │\n"
    "│                                                                 │\n"
    "│ Ova skripta biće uklonjena u v4.0.                            │\n"
    "└─────────────────────────────────────────────────────────────────┘\n",
    DeprecationWarning,
    stacklevel=1,
)

try:
    from vaf.cli import main
    main()
except ImportError:
    # VAF package not installed — try to run with Python path workaround
    import os
    import subprocess
    src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    env = {**os.environ, "PYTHONPATH": src_path + os.pathsep + os.environ.get("PYTHONPATH", "")}
    result = subprocess.run(
        [sys.executable, "-m", "vaf.cli"] + sys.argv[1:],
        env=env,
    )
    sys.exit(result.returncode)
