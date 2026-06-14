# Changelog — Vibe-Audit Framework (VAF)

Sve značajne izmene u ovom projektu biće dokumentovane u ovom fajlu.

Format prati [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
a projekat koristi [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] — 2026-06-14

### Dodato

**Arhitektura i CLI**
- `pyproject.toml` — projekat je sada instalabilan Python paket (`pip install post-vibe-audit` / `pipx install post-vibe-audit`)
- `vaf` CLI sa subkomandama: `pack`, `scan`, `report`, `verify`, `pr-review`
- `src/vaf/` paket struktura: `cli.py`, `config.py`, `packer.py`, `redaction.py`, `evidence.py`
- `vaf.config.yaml` podrška — svi limiti i liste isključenja su konfigurabilni

**Bezbednost i redakcija tajni**
- `src/vaf/redaction.py` — automatska detekcija i maskiranje tajni pre slanja LLM-u
  - Pokriva: OpenAI/Anthropic/Google API ključevi, GitHub/GitLab tokeni, AWS/GCP/Azure credentials, JWT tokeni, generic high-entropy stringovi
  - Generiše `secrets_report.json` (samo tipovi i broj, nikad vrednosti)
- `src/vaf/evidence.py` — SHA-256 hash index za sve uključene fajlove

**Novi 2026 standardi**
- OWASP ASVS 5.0 (umesto 4.x)
- OWASP Top 10 for LLM Applications 2025
- OWASP Top 10 for Agentic Applications 2026
- Sonar AI Code Assurance (preciznije od generičkog SonarQube)
- Supply chain: SLSA, OpenSSF Scorecard, SBOM provenance

**Persona 4 — AI/Agentic Systems Auditor**
- Nova četvrta perspektiva u `prompts/pro_audit_prompt.md`
- Pokriva: LLM/agent/tool calling/RAG/memory rizike, prompt injection, least privilege za AI alate, human approval za destruktivne akcije
- Novi finding ID format: `AI-NNN`, `AGT-NNN`
- Agentic/Tool Boundary Matrix tabela u izveštaju

**Output formati**
- `src/vaf/reporters/json_reporter.py` — strukturovani JSON findings
- `src/vaf/reporters/sarif_reporter.py` — SARIF 2.1.0 za GitHub Code Scanning
- `src/vaf/reporters/markdown_reporter.py` — refaktorisani MD reporter

**Automatsko pokretanje skenera**
- `src/vaf/scanners/trivy.py` — vuln/misconfig/secret/license scan
- `src/vaf/scanners/bandit.py` — Python AST bezbednosna analiza
- `src/vaf/scanners/semgrep.py` — pattern-based SAST
- `src/vaf/scanners/gitleaks.py` — git historija secrets scan

**PR review mode**
- `src/vaf/pr_review.py` — `vaf pr-review --base main --head HEAD`
- Identifikuje dotaknute oblasti, procenjuje rizik, upozorava na test gap

**Pakovanje strategije**
- `deep` (default), `quick`, `security-first`, `changed-files`, `architecture`
- File importance scoring: auth > api > middleware > db > config > tests > docs

**CI/CD integracija**
- `.github/workflows/ci.yml` — pytest, ruff, mypy, end-to-end pack test
- `.github/workflows/vaf-action-template.yml` — kompletni VAF PR audit template

**Licenca i projekat**
- `LICENSE` (MIT) — firme mogu slobodno koristiti
- `SECURITY.md` — responsible disclosure politika
- `CONTRIBUTING.md` — upustvo za kontributore
- `CHANGELOG.md` — ovaj fajl

**Testovi**
- `tests/test_redaction.py`, `test_packer.py`, `test_config.py`
- `tests/fixtures/` — node_project, python_project, secret_leak_project

### Izmenjeno

- `prompts/pro_audit_prompt.md` — ažurirani standardi (ASVS 5.0, LLM 2025, Agentic 2026), dodata Persona 4
- `.cursorrules` — dodata AI/Agentic sekcija, ažurirani standardi
- `README.md` — kompletno prepisan; pozicioniranje kao DevSecOps framework
- `.gitignore` — dodati VAF scan output direktorijumi

### Zastarelo (Deprecated)

- `scripts/vibe_audit_packer.py` — zadržano kao deprecated wrapper koji poziva `vaf pack`; biće uklonjeno u v4.0

---

## [2.0.0] — 2025 (retroaktivno dokumentovano)

### Dodato

- Pro Audit Mega-Prompt sa tri persone (Security, Architecture, QA)
- `scripts/vibe_audit_packer.py` — context packer skripta
- Šabloni: `finding_template.md`, `adr_template.md`, `scope_matrix_template.md`
- `.cursorrules` za Cursor/Cline/Copilot
- OWASP Top 10:2025, OWASP API Security Top 10:2023, WCAG 2.2 AA, GDPR integracija

---

*Format: [Semantic Versioning](https://semver.org/) | [Keep a Changelog](https://keepachangelog.com/)*
