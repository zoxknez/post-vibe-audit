# Vibe-Audit Framework (VAF) v3.0 🛡️🤖

[English version below](#english-version-)

**Sveobuhvatni DevSecOps okvir i CLI alat za višedimenzionalnu reviziju softvera nastalog AI-potpomognutim ("vibe") kodiranjem.**

VAF v3.0 transformiše proces provere iz običnog prompt-skript šablona u ozbiljan bezbednosni alat integrisan u vaš CI/CD pipeline. Pomaže AI modelima (Gemini, Claude, ChatGPT, Cursor, Cline) da obave kompletnu, dokazima potkrijepljenu proveru aplikacije iz četiri nezavisne perspektive kako bi se sprečio LLM "tunelski vid".

---

## Ključne Novine u v3.0

- **Jednostavan CLI Alat**: Instalirajte ga sa `pip install -e .` i upravljajte auditom preko komande `vaf`.
- **Konfigurabilnost (`vaf.config.yaml`)**: Prilagodite limite, dozvoljene fajlove, ignorisane direktorijume, bezbednosne gate-ove i aktivne skenere.
- **Secrets Firewall (Redakcija Tajni)**: Automatski detektuje i uklanja API ključeve, JWT tokene, lozinke i druge tajne pre pakovanja koda. Generiše bezbedan `secrets_report.json` bez curenja stvarnih vrednosti.
- **Tamper-Evident Index (`evidence_index.json`)**: Izračunava SHA-256 heševe za svaki uključeni fajl kako bi se olakšala post-audit verifikacija.
- **Anti-Halucinaciona Verifikacija (`vaf verify`)**: Proverava LLM izveštaj i potvrđuje da li svi referencirani fajlovi i linije koda zaista postoje u evidence indeksu.
- **Integracija Alata (`vaf scan`)**: Automatski pokreće i normalizuje rezultate eksternih skenera poput Trivy, Bandit, Semgrep i Gitleaks.
- **Multi-Format Reports (`vaf report`)**: Generiše izveštaje u Markdown, JSON i standardnom SARIF 2.1.0 formatu za direktan upload na GitHub Code Scanning.
- **PR Review Mode (`vaf pr-review`)**: Analizira git diff i pruža procenu rizika za touchovane oblasti pre merge-ovanja.

---

## Sadržaj Repozitorijuma

```
.
├── .github/workflows/
│   ├── ci.yml                    ← GitHub Actions CI konfiguracija
│   └── vaf-action-template.yml   ← Šablon za PR VAF bezbednosnu proveru
├── .cursorrules                  ← Pravila za AI asistente (Cursor, Cline) ažurirana za v3.0
├── llms.txt                      ← LLM mapa projekta za lakše razumevanje steka
├── pyproject.toml                ← Python konfiguracija pakovanja, Ruff i Mypy pravila
├── README.md                     ← Ova dokumentacija
├── vaf.config.example.yaml       ← Primer konfiguracije projekta
├── prompts/
│   └── pro_audit_prompt.md       ← ⭐ Pro Mega-Prompt v3.0 (OWASP 2025/2026, Persona 4)
├── scripts/
│   └── vibe_audit_packer.py      ← Deprecated wrapper skripta radi kompatibilnosti
├── src/vaf/                      ← Izvorni kod alata
│   ├── cli.py                    ← CLI argumenti i ruter komandi
│   ├── config.py                 ← Učitavanje i validacija vaf.config.yaml
│   ├── packer.py                 ← Glavna logika za pakovanje koda
│   ├── redaction.py              ← Secrets Firewall i detekcija entropije
│   ├── evidence.py               ← Generisanje evidence indeksa
│   ├── verifier.py               ← Anti-halucinacioni verifikator
│   ├── pr_review.py              ← PR diff i risk analizator
│   ├── reporters/                ← Markdown, JSON i SARIF generatori
│   └── scanners/                 ← Integracije za Trivy, Bandit, Semgrep, Gitleaks
├── templates/                    ← Šabloni za ručne nalaze, ADR-ove i matrice
└── tests/                        ← Unit i integracioni testovi
```

---

## Instalacija

Klonirajte repozitorijum i instalirajte paket u lokalnom okruženju:

```bash
# Kreiranje i aktiviranje virtuelnog okruženja
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # Linux/macOS

# Instalacija paketa u editable modu sa dev alatima
pip install -e ".[dev]"
```

---

## Komandni Vodič (CLI)

### 1. Pakovanje konteksta (`vaf pack`)
Prikuplja fajlove projekta, detektuje tehnološki stek, generiše stablo direktorijuma i kreira bezbedan `CURRENT_CONTEXT.md` bundle.

```bash
# Podrazumevano pakovanje celog projekta (deep mode)
vaf pack

# Brzo pakovanje (quick mode) - fokusira se samo na kritične fajlove
vaf pack --mode quick

# Pakovanje sa specifičnom strategijom (npr. samo fajlovi vezani za bezbednost)
vaf pack --strategy security-first

# Isključivanje redakcije tajni (⚠️ pažnja: ne preporučuje se)
vaf pack --no-redact
```

### 2. Automatsko skeniranje (`vaf scan`)
Pokreće podržane bezbednosne alate na projektu.

```bash
# Pokretanje svih detektovanih skenera
vaf scan

# Pokretanje samo specifičnih alata
vaf scan --tools bandit,semgrep

# Neuspeh procesa (exit code 1) ako se pronađu Critical/High nalazi
vaf scan --fail-on-high
```

### 3. Generisanje izveštaja (`vaf report`)
Konvertuje rezultate automatskog skeniranja u strukturisane formate.

```bash
# Generisanje podrazumevanog Markdown izveštaja
vaf report

# Generisanje JSON i SARIF izveštaja za GitHub Code Scanning
vaf report --format json,sarif
```

### 4. PR Risk Analiza (`vaf pr-review`)
Daje bezbednosnu procenu izmena pre spajanja PR-a.

```bash
vaf pr-review --base main --head HEAD
```

### 5. Verifikacija LLM izveštaja (`vaf verify`)
Proverava da li su nalazi iz LLM audit izveštaja konzistentni sa fajlovima u indeksu dokaza.

```bash
vaf verify .vibe_audit/audit_report.md
```

---

## Ugrađene Persone i Standardi (v3.0)

U `prompts/pro_audit_prompt.md` integrisane su četiri nezavisne persone za pregled:

1. **Senior Application Security Auditor**:
   - OWASP Top 10:2025, OWASP API Security Top 10:2023, OWASP ASVS 5.0 (Application Security Verification Standard, maj 2025).
   - Supply chain analize: OpenSSF Scorecard, SLSA, SBOM provera.
2. **Principal Systems Architect**:
   - Sonar AI Code Assurance standardi (0 novih Critical/High, ≥80% coverage, ≤3% dupliranje).
   - SOLID principi, tehnički dug i kompleksnost.
3. **QA & Business Logic Analyst**:
   - WCAG 2.2 AA standard pristupačnosti (9 novih kriterijuma).
   - GDPR usklađenost (Čl. 25, 30, 32).
4. **AI/Agentic Systems Auditor** [NOVO v3.0]:
   - OWASP LLM Top 10:2025 i OWASP Agentic Top 10:2026.
   - Analiza rizika prompt injection-a, indirect prompt injection-a, tool permissions i human approval kontrola.

---

## CI/CD Integracija

Primer postavljanja VAF bezbednosnih provera u GitHub Actions nalazi se u fajlu [.github/workflows/vaf-action-template.yml](file:///d:/ProjektiApp/analizaprojekta/.github/workflows/vaf-action-template.yml). On automatski pakuje projekat, pokreće skenere, eksportuje SARIF i dodaje komentar sa verdict-om direktno na vaš Pull Request.

---

<div id="english-version-"></div>

# Vibe-Audit Framework (VAF) v3.0 🛡️🤖 (English)

**Comprehensive DevSecOps framework and CLI tool for multi-dimensional software audits of AI-assisted ("vibe coded") applications.**

VAF v3.0 transforms the review process from a basic prompt-packer script into an installable security utility integrated into your CI/CD pipeline. It guides AI models (Gemini, Claude, ChatGPT, Cursor, Cline) to perform complete, evidence-based code audits from four independent perspectives to prevent LLM "tunnel vision."

---

## Key Features in v3.0

- **CLI-Driven Audit Suite**: Run your audit with the `vaf` CLI command after running `pip install -e .`.
- **Configurable (`vaf.config.yaml`)**: Manage limits, file exclusions, security gates, and scanners from a project configuration file.
- **Secrets Firewall (Redaction)**: Automatically masks API keys, JWT tokens, passwords, and private credentials before packaging. Outputs a safe `secrets_report.json` detailing found risk types without leaking values.
- **Tamper-Evident Index (`evidence_index.json`)**: Builds SHA-256 hashes of all included files to ensure the audit findings map to code that was actually analyzed.
- **Anti-Hallucination Verification (`vaf verify`)**: Checks LLM findings to verify that referenced files, functions, and lines actually exist within the evidence index.
- **Scanners Pipeline (`vaf scan`)**: Integrates and normalizes outputs from Trivy, Bandit, Semgrep, and Gitleaks.
- **Multi-Format Exporters (`vaf report`)**: Exports results to Markdown summaries, structured JSON, or standard SARIF 2.1.0 to upload findings directly to GitHub Code Scanning.
- **PR Review Mode (`vaf pr-review`)**: Analyzes git diffs and alerts developers of security-critical changes or testing gaps before merging.

---

## Quick Start

### 1. Install VAF
```bash
git clone https://github.com/zoxknez/post-vibe-audit.git
cd post-vibe-audit
pip install -e ".[dev]"
```

### 2. Package and Audit
```bash
# Package code context (masks secrets, writes evidence index)
vaf pack

# Run automated scanners (e.g. Semgrep, Bandit)
vaf scan

# Export reports in Markdown and SARIF formats
vaf report --format markdown,sarif
```

### 3. Review findings with LLM
Upload `.vibe_audit/CURRENT_CONTEXT.md` alongside the instructions in `prompts/pro_audit_prompt.md` to Claude, Gemini Pro, or your favorite AI interface.

---

## Embedded Personas & Standards

1. **Senior Application Security Auditor**: OWASP Top 10:2025, OWASP API Security:2023, OWASP ASVS 5.0, supply-chain checks (OpenSSF, SLSA).
2. **Principal Systems Architect**: Sonar AI Code Assurance guidelines, SOLID principles, technical debt.
3. **QA & Business Logic Analyst**: WCAG 2.2 AA accessibility, GDPR (Articles 25/30/32) privacy by design.
4. **AI/Agentic Systems Auditor** [NEW v3.0]: OWASP LLM Top 10:2025, OWASP Agentic Top 10:2026, prompt injection risks, tool execution permissions.

---

## License

This project is licensed under the MIT License - see the [LICENSE](file:///d:/ProjektiApp/analizaprojekta/LICENSE) file for details.
