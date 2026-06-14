"""
VAF CLI — Vibe-Audit Framework Command Line Interface

Usage:
    vaf pack [--path .] [--mode deep|quick] [--strategy deep|quick|security-first|changed-files|architecture]
    vaf scan [--tools trivy,bandit,semgrep,gitleaks] [--path .]
    vaf report [--input .vibe_audit/] [--format md,json,sarif]
    vaf verify <audit_report.md>
    vaf pr-review [--base main] [--head HEAD]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _print_banner() -> None:
    print("""
╔══════════════════════════════════════════════════╗
║   Vibe-Audit Framework (VAF) v3.0               ║
║   DevSecOps audit za AI-generisani kod          ║
╚══════════════════════════════════════════════════╝
""")


# ─── Pack command ──────────────────────────────────────────────────────────────

def cmd_pack(args: argparse.Namespace) -> int:
    """Pack repository context into LLM-ready bundle."""
    from vaf.config import load_config
    from vaf.packer import pack

    root_dir = Path(args.path).resolve() if args.path else Path.cwd()
    if not root_dir.exists():
        print(f"[VAF] GREŠKA: direktorijum ne postoji: {root_dir}", file=sys.stderr)
        return 1

    config = load_config(root_dir)

    # CLI args override config
    if args.mode:
        config.mode = args.mode
    if args.redact is False:
        config.enable_redaction = False

    strategy = args.strategy or config.mode
    try:
        output_path = pack(
            root_dir=root_dir,
            mode=config.mode,
            strategy=strategy,
            config=config,
            verbose=not args.quiet,
        )
        if not args.quiet:
            print(f"\n[VAF] ✅ Context bundle: {output_path}")
        return 0
    except Exception as exc:
        print(f"[VAF] GREŠKA pri pakovanju: {exc}", file=sys.stderr)
        return 1


# ─── Scan command ──────────────────────────────────────────────────────────────

def cmd_scan(args: argparse.Namespace) -> int:
    """Run automated security scanners."""
    from vaf.config import load_config
    from vaf.scanners import run_scanners

    root_dir = Path(args.path).resolve() if args.path else Path.cwd()
    config = load_config(root_dir)

    tools = [t.strip() for t in args.tools.split(",")] if args.tools else config.enabled_scanners

    if not args.quiet:
        print(f"[VAF] Pokretanje skenera: {', '.join(tools)}")

    results = run_scanners(root_dir, tools, config)
    failed = False

    for tool, result in results.items():
        status_icon = "✅" if result["status"] == "executed" else "⚠️" if result["status"] == "skipped" else "❌"
        findings_count = len(result.get("findings", []))
        print(f"  {status_icon} {tool}: {result['status']} — {findings_count} nalaza")

        if result["status"] == "executed":
            high_count = sum(1 for f in result.get("findings", [])
                            if f.get("severity", "").lower() in ("critical", "high"))
            if high_count > 0:
                print(f"     ⚠️  {high_count} Critical/High nalaza!")
                failed = args.fail_on_high

    if failed:
        print("\n[VAF] ❌ Scan FAILED — Critical/High nalazi pronađeni.", file=sys.stderr)
        return 1

    print("\n[VAF] ✅ Scan završen. Rezultati: .vibe_audit/scans/")
    return 0


# ─── Report command ────────────────────────────────────────────────────────────

def cmd_report(args: argparse.Namespace) -> int:
    """Generate structured reports from findings."""
    from vaf.reporters import generate_reports

    input_dir = Path(args.input).resolve()
    if not input_dir.exists():
        print(f"[VAF] GREŠKA: input direktorijum ne postoji: {input_dir}", file=sys.stderr)
        return 1

    formats = [f.strip() for f in args.format.split(",")] if args.format else ["markdown"]
    output_dir = Path(args.output).resolve() if args.output else input_dir

    try:
        generated = generate_reports(input_dir, output_dir, formats)
        for path in generated:
            print(f"[VAF] ✅ Report generisan: {path}")
        return 0
    except Exception as exc:
        print(f"[VAF] GREŠKA pri generisanju reporta: {exc}", file=sys.stderr)
        return 1


# ─── Verify command ────────────────────────────────────────────────────────────

def cmd_verify(args: argparse.Namespace) -> int:
    """Anti-hallucination verifier for audit reports."""
    from vaf.verifier import verify_report

    report_path = Path(args.report).resolve()
    if not report_path.exists():
        print(f"[VAF] GREŠKA: report fajl ne postoji: {report_path}", file=sys.stderr)
        return 1

    evidence_path = report_path.parent / "evidence_index.json"
    issues = verify_report(report_path, evidence_path if evidence_path.exists() else None)

    if not issues:
        print("[VAF] ✅ Verifikacija prošla — svi nalazi su konzistentni.")
        return 0

    print(f"[VAF] ⚠️ Pronađeno {len(issues)} problema u izveštaju:\n")
    for issue in issues:
        print(f"  {issue}")
    return 1


# ─── PR review command ─────────────────────────────────────────────────────────

def cmd_pr_review(args: argparse.Namespace) -> int:
    """Analyze a pull request diff for risks."""
    from vaf.config import load_config
    from vaf.pr_review import review_pr

    root_dir = Path(args.path).resolve() if args.path else Path.cwd()
    config = load_config(root_dir)

    try:
        summary = review_pr(
            root_dir=root_dir,
            base=args.base,
            head=args.head,
            config=config,
        )
        print(summary)
        return 0
    except Exception as exc:
        print(f"[VAF] GREŠKA pri PR review-u: {exc}", file=sys.stderr)
        return 1


# ─── Main entry point ──────────────────────────────────────────────────────────

def main() -> None:
    """VAF CLI entry point."""
    # UTF-8 for Windows compatibility
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="vaf",
        description="Vibe-Audit Framework v3.0 — DevSecOps audit za AI-generisani kod",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Primeri:
  vaf pack                                   # pakuj trenutni projekat
  vaf pack --path ./my-project --mode quick  # brza provera drugog projekta
  vaf pack --strategy security-first         # samo security-relevantni fajlovi
  vaf scan --tools trivy,bandit              # pokreni skenere
  vaf report --format json,sarif             # generiši JSON i SARIF reporte
  vaf verify .vibe_audit/audit_report.md     # verifikuj LLM izveštaj
  vaf pr-review --base main                  # analiziraj PR diff
        """,
    )
    parser.add_argument("--version", action="version", version="VAF v3.0.0")

    subparsers = parser.add_subparsers(dest="command", metavar="<komanda>")
    subparsers.required = True

    # ── pack ──
    pack_parser = subparsers.add_parser("pack", help="Pakuj kontekst repozitorijuma u LLM-ready bundle")
    pack_parser.add_argument("--path", "-p", help="Putanja do projekta (default: trenutni direktorijum)")
    pack_parser.add_argument("--mode", "-m", choices=["quick", "deep"], default="deep",
                             help="Režim analize (default: deep)")
    pack_parser.add_argument(
        "--strategy", "-s",
        choices=["deep", "quick", "security-first", "changed-files", "architecture"],
        help="Strategija pakovanja (default: prati mode)",
    )
    pack_parser.add_argument("--no-redact", dest="redact", action="store_false", default=True,
                             help="Isključi redakciju tajni (⚠️ pažnja!)")
    pack_parser.add_argument("--quiet", "-q", action="store_true", help="Tihi mode — bez napretka")
    pack_parser.set_defaults(func=cmd_pack)

    # ── scan ──
    scan_parser = subparsers.add_parser("scan", help="Pokreni automatske security skenere")
    scan_parser.add_argument("--path", "-p", help="Putanja do projekta (default: trenutni direktorijum)")
    scan_parser.add_argument("--tools", "-t",
                              help="Skeneri odvojeni zarezom: trivy,bandit,semgrep,gitleaks")
    scan_parser.add_argument("--fail-on-high", action="store_true",
                              help="Exit code 1 ako postoje Critical/High nalazi")
    scan_parser.add_argument("--quiet", "-q", action="store_true")
    scan_parser.set_defaults(func=cmd_scan)

    # ── report ──
    report_parser = subparsers.add_parser("report", help="Generiši strukturovane reporte")
    report_parser.add_argument("--input", "-i", default=".vibe_audit",
                                 help="Ulazni direktorijum sa scan rezultatima (default: .vibe_audit)")
    report_parser.add_argument("--format", "-f", default="markdown",
                                 help="Formati odvojeni zarezom: markdown,json,sarif (default: markdown)")
    report_parser.add_argument("--output", "-o", help="Izlazni direktorijum (default: isti kao --input)")
    report_parser.set_defaults(func=cmd_report)

    # ── verify ──
    verify_parser = subparsers.add_parser("verify", help="Verifikuj LLM audit izveštaj (anti-hallucination)")
    verify_parser.add_argument("report", metavar="REPORT", help="Putanja do audit report fajla")
    verify_parser.set_defaults(func=cmd_verify)

    # ── pr-review ──
    pr_parser = subparsers.add_parser("pr-review", help="Analiziraj PR diff za rizike")
    pr_parser.add_argument("--path", "-p", help="Putanja do projekta (default: trenutni direktorijum)")
    pr_parser.add_argument("--base", "-b", default="main", help="Base branch (default: main)")
    pr_parser.add_argument("--head", "-H", default="HEAD", help="Head branch/commit (default: HEAD)")
    pr_parser.set_defaults(func=cmd_pr_review)

    args = parser.parse_args()

    if not args.quiet if hasattr(args, "quiet") else True:
        _print_banner()

    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
