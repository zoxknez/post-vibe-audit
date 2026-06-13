# Vibe-Audit Framework (VAF) v2.0 🛡️🤖

[English version below](#english-version-)

**Sveobuhvatni okvir za višedimenzionalnu reviziju softvera nastalog vibe kodiranjem.**

VAF omogućava svakom AI modelu (Gemini, Claude, ChatGPT, Cursor, Cline) da obavi kompletnu, dokazima potkrijepljenu analizu aplikacije iz tri nezavisne perspektive — bez "tunelskog vida". Sadrži Pro Mega-Prompt sa ugrađenim standardima OWASP Top 10:2025, OWASP API Security Top 10:2023, WCAG 2.2 AA i GDPR Čl.25/30/32.

---

## Zašto VAF?

Kada "vibe kodirate" (brzo generišete aplikacije kroz AI), zaobilazite tradicionalno razvojno trenje: peer review, unit testove, dokumentovanje arhitekture. VAF veštački ponovo uvodi to trenje u fazi verifikacije — strukturisanim promptovanjem, automatizovanim pakovanjem konteksta i standardizovanim šablonima za nalaze.

**Ključni problem koji VAF rešava**: LLM-ovi pate od "tunelskog vida" — kada dobiju generičan zahtev "proveri kod", fokusiraju se na jednu dimenziju (obično sintaksu) i ignorišu bezbednost, arhitekturu i poslovnu logiku. VAF primorava model na tri nezavisne persone i samokorekciju.

---

## Sadržaj Repozitorijuma

```
.
├── .cursorrules                  ← Pravila za AI editore (Cursor, Cline, Copilot)
├── llms.txt                      ← LLM mapa projekta
├── README.md                     ← Ova dokumentacija
├── prompts/
│   └── pro_audit_prompt.md       ← ⭐ GLAVNI DELIVERABLE — Pro Mega-Prompt
├── scripts/
│   └── vibe_audit_packer.py      ← Skripta za automatsko pakovanje konteksta
├── templates/
│   ├── adr_template.md           ← Šablon za Architecture Decision Records
│   ├── scope_matrix_template.md  ← Šablon za inventar artefakata
│   └── finding_template.md       ← Šablon za dokumentovanje nalaza
└── .vibe_audit/                  ← Generisani output (gitignore!)
    ├── CURRENT_CONTEXT.md        ← LLM-ready paket (auto-generisano)
    └── adrs/                     ← Arhiva ADR-ova
```

---

## Brzo Pokretanje (3 koraka)

### Korak 1: Kopirajte u vaš projekat
```bash
# Kopirajte sledeće fajlove u koren vašeg projekta:
.cursorrules
llms.txt
prompts/pro_audit_prompt.md
scripts/vibe_audit_packer.py
templates/
```

### Korak 2: Pokrenite pakovanje konteksta
```bash
# Dubinska analiza (preporučeno)
python scripts/vibe_audit_packer.py

# Brza provera
python scripts/vibe_audit_packer.py --mode quick

# Za drugi projekat
python scripts/vibe_audit_packer.py --path /putanja/do/projekta
```

### Korak 3: Pokrenite audit
Prevucite `.vibe_audit/CURRENT_CONTEXT.md` u:
- **Claude 3.5/4.x** — povucite fajl direktno u chat (preporučeno za dugi kontekst)
- **Gemini 1.5/2.x Pro** — uploadujte fajl
- **ChatGPT-4o** — kopirajte sadržaj ili uploadujte
- **Cursor Agent** — `@codebase` + sadržaj fajla
- **Cline** — pokrenite novu sesiju i priložite fajl

---

## Šta Dobijate kao Izlaz

AI primenjuje protokol sa tri persone i isporučuje:

| Sekcija | Sadržaj |
|---|---|
| **Executive Summary** | 3 rečenice: šta je provereno, najveći rizici, go/no-go |
| **Scope & Artefakt Matrica** | Šta je dostavljeno, šta je `unspecified` |
| **Finding Matrix** | Svi nalazi po domenima, prioritetima i severity |
| **Detaljni Nalazi** | ID, dokaz, OWASP mapiranje, reprodukcija, fix, primer koda |
| **Mermaid Dijagram** | Vizualizacija toka analize |
| **Top 5 Prioriteta** | P0/P1 nalazi koje treba popraviti pre produkcije |
| **Metrički Grafici** | p95 latencija, error rate, coverage (ako postoje podaci) |
| **Unspecified Data** | Šta nedostaje i šta bi povećalo bezbednost zaključaka |
| **Go/No-Go Verdict** | `go` / `conditional go` / `no-go` sa obrazloženjem |

---

## Ugrađeni Standardi

### Bezbednost
| Standard | Verzija | Opis |
|---|---|---|
| OWASP Top 10 | **2025** (A01–A10) | Novi: A03 Supply Chain Failures, A10 Exceptional Conditions |
| OWASP API Security | **2023** (API1–API10) | BOLA, BFLA, Unrestricted Consumption, SSRF |
| OWASP ASVS | 4.x | Tehničke security kontrole |
| Trivy | 0.50+ | `--scanners vuln,misconfig,secret,license` |
| Bandit | 1.7+ | AST analiza Python koda |
| OWASP ZAP | Stable | Baseline, full-scan, api-scan (OpenAPI, GraphQL) |

### Kvalitet i Arhitektura
| Standard/Alat | Opis |
|---|---|
| SonarQube "Sonar way for AI Code" | AI-specifični quality gate: 0 novih Critical/High, ≥80% coverage, ≤3% duplikat |
| ESLint CLI | `--format json` za CI integraciju |
| pytest + pytest-cov | JUnit XML + HTML/XML/JSON coverage |
| JaCoCo Maven | `mvn test jacoco:report` / `mvn verify` |

### Performanse
| Alat | Komanda |
|---|---|
| Locust | `--headless -u N -r R --run-time Xm --html --json-file --csv` |
| JMeter | `-n -t test.jmx -l results.jtl -e -o report-dir/` |
| Prometheus + Grafana | p50/p95/p99, throughput, error rate, saturation |

### Pristupačnost i Privacy
| Standard | Verzija | Ključni kriteriji |
|---|---|---|
| WCAG | **2.2 AA** | 9 novih kriterija: 2.4.11, 2.4.13, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8 |
| Lighthouse | Latest | `--only-categories=accessibility,performance` |
| GDPR | EU 2016/679 | Čl.25 Privacy by Design, Čl.30 RoPA, Čl.32 Security of Processing |

---

## Status Nalaza — Kodovi

| Status | Značenje |
|---|---|
| `executed` | Provera je zaista izvršena, postoji konkretan dokaz |
| `inferred` | Zaključeno iz koda/konfiguracije/artefakata bez direktnog izvršavanja |
| `blocked` | Nije moglo biti provereno zbog nedostajućih podataka/pristupa |
| `not_applicable` | Nije primenjivo na ovaj stek/aplikaciju |

---

## Korišćenje Architecture Decision Records (ADR)

Svaka važna arhitektonska odluka treba biti dokumentovana:

```bash
# 1. Kopirajte šablon
cp templates/adr_template.md .vibe_audit/adrs/0001-my-decision.md

# 2. Popunite šablon
# 3. Kod sledećeg pokretanja packer-a, ADR će biti automatski uključen u kontekst
python scripts/vibe_audit_packer.py
```

Primjeri ADR naslova:
- `0001-prevent-sql-injection-parameterized-queries.md`
- `0002-jwt-validation-server-side-only.md`
- `0003-rate-limiting-auth-endpoints.md`
- `0004-gdpr-data-retention-90-days.md`

---

## Integrisanje u CI/CD Pipeline

Primjer GitHub Actions workflow-a:

```yaml
name: VAF Audit

on:
  pull_request:
    branches: [main, develop]

jobs:
  vibe-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trivy Security Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          scanners: 'vuln,secret,misconfig'
          format: 'sarif'
          output: 'trivy-results.sarif'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy Results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Generate VAF Context Bundle
        run: python scripts/vibe_audit_packer.py

      - name: Upload VAF Context as Artifact
        uses: actions/upload-artifact@v4
        with:
          name: vibe-audit-context
          path: .vibe_audit/CURRENT_CONTEXT.md
```

---

<div id="english-version-"></div>

# Vibe-Audit Framework (VAF) v2.0 🛡️🤖 (English)

**Comprehensive multi-dimensional software audit framework for AI-assisted ("vibe coded") applications.**

VAF enables any LLM (Gemini, Claude, ChatGPT, Cursor, Cline) to perform a complete, evidence-based audit from three independent perspectives — eliminating tunnel vision. Includes a Pro Mega-Prompt with embedded OWASP Top 10:2025, OWASP API Security Top 10:2023, WCAG 2.2 AA, and GDPR Art.25/30/32 standards.

---

## Quick Start

### Step 1: Copy to your project
Copy `.cursorrules`, `llms.txt`, `prompts/pro_audit_prompt.md`, `scripts/vibe_audit_packer.py`, and the `templates/` directory to your project root.

### Step 2: Package the context
```bash
# Deep analysis (recommended)
python scripts/vibe_audit_packer.py

# Quick check mode
python scripts/vibe_audit_packer.py --mode quick

# Target a different project path
python scripts/vibe_audit_packer.py --path /path/to/project
```

### Step 3: Run the audit
Drag `.vibe_audit/CURRENT_CONTEXT.md` into Claude, Gemini, ChatGPT, or any LLM.

The AI will automatically:
1. Build a scope & artifact matrix
2. Run Persona 1: Senior Application Security Auditor (OWASP Top 10:2025 + API Security:2023)
3. Run Persona 2: Principal Systems Architect (SonarQube AI Code gate, SOLID, tech debt)
4. Run Persona 3: QA & Business Logic Analyst (error handling, WCAG 2.2, GDPR)
5. Apply self-critique to eliminate anchoring bias and halo effect
6. Deliver a structured report with go/conditional go/no-go verdict

---

## Embedded Standards (all current as of 2025)

- **OWASP Top 10:2025** — A01 Broken Access Control through A10 Mishandling of Exceptional Conditions
- **OWASP API Security Top 10:2023** — BOLA, Broken Auth, BFLA, SSRF, Improper Inventory Management
- **WCAG 2.2 AA** — All 9 new criteria (2.4.11, 2.4.13, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8)
- **GDPR** — Art.25 Privacy by Design, Art.30 RoPA, Art.32 Security of Processing
- **SonarQube "Sonar way for AI Code"** — Zero new Critical/High, ≥80% coverage, ≤3% duplication
- **Trivy 0.50+** — `--scanners vuln,misconfig,secret,license`
- **Locust headless** — `-u`, `-r`, `--run-time`, `--html`, `--json-file`, `--csv`
