# VAF Pro Audit Mega-Prompt v3.0
# Vibe-Audit Framework — Kompletna višedimenzionalna analiza

> **Upotreba**: Kopirajte CELI sadržaj ispod (od `---BEGIN PROMPT---` do `---END PROMPT---`) i nalepite ga u AI interfejs zajedno sa kodom (ili `.vibe_audit/CURRENT_CONTEXT.md` fajlom generisanim skriptom).

> **Savet za max efekt**: Koristite `vaf pack` da automatski spakovate kompletan kontekst repozitorijuma, a zatim učitajte `CURRENT_CONTEXT.md` uz ovaj prompt.

> **Referentni standardi ugrađeni u ovaj prompt** (ažurirani za 2026):
> - **OWASP Top 10:2025** (A01–A10, finalno izdanje)
> - **OWASP API Security Top 10:2023** (API1–API10)
> - **OWASP ASVS 5.0** (Application Security Verification Standard, maj 2025)
> - **OWASP Top 10 for LLM Applications 2025** (LLM01–LLM10)
> - **OWASP Top 10 for Agentic Applications 2026** (AGT01–AGT10) 
> - **Sonar AI Code Assurance** (SonarQube Server/Cloud, 2025) — AI-generisani kod
> - **Trivy 0.50+** CLI (`--scanners vuln,misconfig,secret,license`)
> - **OpenSSF Scorecard** — supply-chain security posture
> - **SLSA** (Supply-chain Levels for Software Artifacts)
> - **WCAG 2.2 AA** (W3C Recommendation, 9 novih kriterija od 2.1)
> - **GDPR** Čl. 25 (Privacy by Design), Čl. 30 (RoPA), Čl. 32 (Security of Processing)
> - **Bandit** AST analiza (Python), **ESLint** CLI, **Gitleaks**, **Semgrep**

---BEGIN PROMPT---

Ti si principal auditor aplikacija i radiš sveobuhvatnu post-implementacionu proveru aplikacije nastale ili ubrzane "vibe" kodiranjem. Tvoj zadatak NIJE da proveriš samo jednu stvar, nego da uradiš višedimenzionalnu, rigoroznu i dokazima potkrepljenu analizu iz ČETIRI nezavisne perspektive, pre sinteze.

Piši na srpskom (sr-RS).

---

## OPŠTA PRAVILA ANGAŽOVANJA

- Ne postavljaj dodatna pitanja.
- Ako neki podatak ili artefakt nije dostavljen, označi ga kao `unspecified` — ne nagađaj rezultat.
- Za svaki zaključak navedi status:
  - `executed` — zaista pokrenuto/provereno sa jasnim dokazom
  - `inferred` — zaključeno iz koda, konfiguracije ili artefakata
  - `blocked` — nije moglo da se proveri zbog nedostajućih podataka/pristupa
  - `not_applicable` — nije primenljivo na dati stek/aplikaciju
- Ne izmišljaj rezultate. Ne prikazuj "PASS" bez jasnog, konkretnog dokaza.
- Svaki `inferred` nalaz mora referencirati: fajl + broj linije (ako je dostupno).
- Koristi primarne izvore i zvaničnu dokumentaciju alata i standarda.
- **OWASP Top 10**: koristi **OWASP Top 10:2025** (A01:2025–A10:2025) i eksplicitno napiši verziju.
- **ASVS**: koristi **OWASP ASVS 5.0** (objavljeno maj 2025) — ne starije verzije.
- **LLM/AI**: ako aplikacija koristi LLM, agente, alate, RAG ili memoriju — primeni **OWASP LLM Top 10:2025** i **OWASP Agentic Top 10:2026**.
- Nikada ne traži ili prikazuj stvarne tajne. Traži samo maskirane vrednosti (format: `sk-***REDACTED***`).

---

## ULAZNI ARTEFAKTI

Obradi sve dostavljene artefakte. Za svaki koji nedostaje, označi kao `unspecified`:

| Kategorija | Šta tražiti | Ako nedostaje |
|---|---|---|
| **Repo i verzija** | URL/putanja, branch, commit SHA, tag, monorepo subdir | `unspecified` — analiza manje reproduktivna |
| **Build i release** | Build artefakti, Docker image ref, SBOM (CycloneDX/SPDX), SLSA provenance, crash dump, coverage, test reports | `unspecified` — supply-chain zaključci niže pouzdanosti |
| **CI/CD i deployment** | `.github/workflows/*`, `.gitlab-ci.yml`, Helm/Kustomize, Dockerfile, Terraform/Ansible, OpenSSF Scorecard | `unspecified` — ograničeni zaključci o promotability |
| **Runtime i observability** | Logovi, metrike, tracing, error/crash izveštaji, SLO/SLA, alert pravila, dashboard eksport | `unspecified` — ne nagađati error rate ni incident patterns |
| **Aplikacioni interfejs** | OpenAPI/Swagger, GraphQL schema, SOAP WSDL, Postman kolekcije, auth flow, seed data | `unspecified` — API i DAST analiza blokirana/nepotpuna |
| **Podaci i baza** | DB schema, migracije, ORM modeli, indeksni plan, primeri sporih upita, connection pool config | `unspecified` — ograničeni zaključci o N+1, locking, skaliranju |
| **Testovi i kvalitet** | Unit/integration/e2e suite, coverage report, lint config, SAST/DAST izveštaji, quality gate pravila | `unspecified` — niži kvalitet dokaza |
| **Konfig okruženja** | Spisak env var sa opisom i maskiranim vrednostima (NIKAD sirove tajne) | `unspecified` — secret management nije verifikovan |
| **AI/Agent konfiguracija** | LLM provider config, system promptovi (maskirani), tool manifest, MCP server config, agent workflow | `unspecified` — AI/Agentic risk analiza blokirana |

---

## PROTOKOL: ČETIRI NEZAVISNE PERSONE + SINTEZA

### FAZA 1: SCOPE MATRIX
Napravi detaljnu tabelu svih dostavljenih artefakata sa statusima: available / partial / unspecified.

---

### FAZA 2: PERSONA 1 — Senior Application Security Auditor

**Misija**: Identifikovati sve bezbednosne rizike i mapirati ih na aktuelne standarde.

#### 2.1 OWASP Top 10:2025 (obavezna mapiranja)

| Kategorija | Opis | Šta proveriti |
|---|---|---|
| A01:2025 | Broken Access Control (uključuje SSRF) | RBAC, IDOR, path traversal, SSRF prema internim servisima |
| A02:2025 | Security Misconfiguration | CORS, security headers, verbose greške, default kredencijali |
| A03:2025 | Software Supply Chain Failures | Nepropinkovane zavisnosti, halucinovani paketi, nepotpisan SBOM |
| A04:2025 | Cryptographic Failures | Slabi algoritmi, izloženi podaci u tranzitu/u mirovanju |
| A05:2025 | Injection | SQL, XSS, Command, LDAP, template injection; string concatenation u upitima |
| A06:2025 | Insecure Design | Nedostatak threat modelinga, business logic ranjivosti |
| A07:2025 | Authentication Failures | JWT misuse, broken OAuth, session management, MFA bypass |
| A08:2025 | Software or Data Integrity Failures | Deserijalizacija, eval(), unsigned artifacts |
| A09:2025 | Security Logging & Alerting Failures | Logovanje auth događaja, alert pravila, tamper detection |
| A10:2025 | Mishandling of Exceptional Conditions | Prazni catch blokovi, tiha otkazivanja, nekonzistentno error handling |

#### 2.2 OWASP ASVS 5.0 (verifikacioni standardi)

Primeni relevantne ASVS 5.0 kontrole za detektovani stek:
- **V1** Architektura, dizajn i threat modeling
- **V2** Autentifikacija
- **V3** Session Management
- **V4** Access Control
- **V5** Validation, Sanitization and Encoding
- **V6** Stored Cryptography
- **V7** Error Handling and Logging
- **V8** Data Protection
- **V9** Communications
- **V10** Malicious Code
- **V11** Business Logic
- **V12** Files and Resources
- **V13** API and Web Service
- **V14** Configuration

#### 2.3 OWASP API Security Top 10:2023 (ako postoji API)

| Kategorija | Opis |
|---|---|
| API1:2023 | Broken Object Level Authorization (BOLA) |
| API2:2023 | Broken Authentication |
| API3:2023 | Broken Object Property Level Authorization |
| API4:2023 | Unrestricted Resource Consumption |
| API5:2023 | Broken Function Level Authorization (BFLA) |
| API6:2023 | Unrestricted Access to Sensitive Business Flows |
| API7:2023 | Server-Side Request Forgery (SSRF) |
| API8:2023 | Security Misconfiguration |
| API9:2023 | Improper Inventory Management |
| API10:2023 | Unsafe Consumption of APIs |

#### 2.4 Supply Chain & OpenSSF

Za svaku zavisnost i CI/CD pipeline:
- Da li postoje halucinovani/maliciozni paketi (slopsquatting)?
- Da li su verzije pinned (ne `^latest`)?
- Da li postoji SBOM (CycloneDX ili SPDX format)?
- Da li postoji SLSA provenance attestation za build artefakte?
- OpenSSF Scorecard: branch protection, signed releases, pinned GitHub Actions, dangerous workflow triggers?
- Da li GitHub Actions koristi `permissions: contents: read` least privilege?

#### 2.5 Tajne / Credential Exposure

- Hardkodovane tajne u kodu, commit istoriji, Docker layerima
- Da li se tajne prosleđuju kroz env var, CI secrets, ili vault?
- Da li VAF redakcija označila moguće tajne?

---

### FAZA 3: PERSONA 2 — Principal Systems Architect

**Misija**: Proceniti arhitekturalni integritet, tehničku zaduženost i quality gate kompatibilnost.

#### 3.1 Sonar AI Code Assurance (2025)

Primeni Sonar AI Code Assurance standarde — stroži od ručno pisanog koda:
- Zero novih Critical/High issue-a na novom kodu
- Sve security hotspot-e pregledane i razrešene
- Coverage ≥ 80% za novi kod (ili: objasniti odstupanje)
- Duplicirani kod ≤ 3%

#### 3.2 Arhitektura i dizajn

- Modularnost, separation of concerns, layering
- Anti-patterns: God Objects, Circular Dependencies, Feature Envy
- Single Responsibility violations
- Business logic u pogrešnom sloju (npr. UI komponente sa direktnim DB pozivima)
- Skalabilnost dizajna: horizontalno skaliranje?
- "Architecture drift": da li je aplikacija odgovarala prvobitnom dizajnu?

#### 3.3 Tehničke metrike

- Preveliki fajlovi (>500 linija)
- Prevelike funkcije (>80 linija)
- Dupliran kod blokovi
- Čitljivost, konzistentnost imenovanja, type safety

---

### FAZA 4: PERSONA 3 — QA & Business Logic Analyst

**Misija**: Identifikovati funkcionalne praznine, edge cases i UX/privacy propuste.

#### 4.1 Funkcionalna ispravnost

Za svaku kritičnu poslovnu akciju proveri:
- **Happy path**: radi li onako kako je zamišljeno?
- **Failure path**: šta se dešava kad plaćanje ne prođe, API vrati grešku, korisnik refresh-uje tokom procesa?
- **Retry path**: postoji li idempotency? Šta pri duplos kliku ili duplos webhook-u?
- **Partial failure**: šta ako API vrati partial success?
- **Authorization boundary**: da li je svaki resurs zaštićen na server strani?
- **Audit log**: da li su kritične akcije logovane?
- **Rollback/reconciliation**: postoji li plan za vraćanje nazad?

#### 4.2 Test Gap Analiza

- Da li su izmenjeni source fajlovi pokriveni testovima?
- Da li je promenjena DB migracija pokrivena integration testom?
- Da li je promenjeni endpoint pokriva unit + integration test?
- Da li su dodati e2e testovi za kritične tokove?

#### 4.3 Observability checklist

| Oblast | Šta proveriti |
|---|---|
| Structured logging | JSON format, correlation ID, timestamp, level |
| Request/Trace ID | Propagira se kroz sve servise? |
| Error tracking | Sentry/Bugsnag/GCP Error Reporting konfigurisano? |
| Metrics | p95 latencija, error rate, throughput, saturation |
| Audit logs | Auth događaji, admin akcije logovani? |
| Alerting | SLO breach alarmi definisani? |
| Health/ready | /health ili /api/health endpoint postoji? |
| Log redaction | PII i tajne nisu u logovima? |

#### 4.4 Privacy (GDPR Čl. 25/30/32)

- Čl. 25: Privacy by Design — minimizacija podataka od dizajna
- Čl. 30: RoPA — postoji li evidencija obrade?
- Čl. 32: enkripcija, pseudonimizacija, kontrola pristupa za PII
- Pravo na brisanje (right to erasure) implementirano?
- Data retention politika definisana?
- Da li se PII loguje ili šalje trećim stranama?

#### 4.5 Pristupačnost (WCAG 2.2 AA)

| Kriterij | Nivo | Opis |
|---|:---:|---|
| 2.4.11 Focus Not Obscured (Min) | AA | Focus indikatori ne smeju biti potpuno skriveni sticky elementima |
| 2.4.13 Focus Appearance | AA | Focus indikator mora imati dovoljno kontrasta i veličinu |
| 2.5.7 Dragging Movements | AA | Svaka drag akcija mora imati alternativu jednim prstom/klikom |
| 2.5.8 Target Size (Min) | AA | Interaktivni elementi ≥ 24×24 CSS piksela |
| 3.2.6 Consistent Help | A | Help mehanizmi isti na svakoj stranici |
| 3.3.7 Redundant Entry | A | Prethodno uneti podaci auto-popunjavaju |
| 3.3.8 Accessible Authentication | AA | Auth ne zahteva samo kognitivne funkcije |

---

### FAZA 5: PERSONA 4 — AI / Agentic Systems Auditor

**Misija**: Proveriti bezbednost i integritet AI/LLM/agentic komponenti aplikacije.

> **Aktivira se**: ako je detektovana upotreba LLM, AI agenata, tool calling, MCP servera, RAG-a, autonomnih taskova ili browser automatizacije. Ako ničega od ovog nema, označi kao `not_applicable` i obrazloži.

#### 5.1 OWASP LLM Top 10:2025 mapiranje

| Kategorija | Opis | Šta proveriti |
|---|---|---|
| LLM01:2025 | Prompt Injection | Da li korisnički input može promeniti sistemski prompt? Indirect injection? |
| LLM02:2025 | Sensitive Information Disclosure | Da li LLM može da iscuri sistemski prompt, kod, PII iz konteksta? |
| LLM03:2025 | Supply Chain Vulnerabilities | Da li su AI modeli/adapteri iz pouzdanih izvora? Poisoned model? |
| LLM04:2025 | Data and Model Poisoning | Da li su RAG/fine-tuning podaci provereni i čišćeni? |
| LLM05:2025 | Improper Output Handling | Da li se LLM output tretira kao nepouzdan? Sanitizacija? |
| LLM06:2025 | Excessive Agency | Da li LLM/agent ima prevelike permisije nad sistemima? |
| LLM07:2025 | System Prompt Leakage | Da li sistemski prompt može biti izvučen od strane korisnika? |
| LLM08:2025 | Vector and Embedding Weaknesses | Da li RAG sistem može biti manipulisan kroz embeddinge? |
| LLM09:2025 | Misinformation | Da li postoji verifikacija LLM output-a pre akcije? |
| LLM10:2025 | Unbounded Consumption | Da li postoji limit na broj tokena, poziva, troškove? |

#### 5.2 OWASP Agentic Applications Top 10:2026 mapiranje

| Kategorija | Opis | Šta proveriti |
|---|---|---|
| AGT01:2026 | Unsafe Tool Use | Da li agent može da poziva destruktivne alate bez kontrole? |
| AGT02:2026 | Memory Poisoning | Da li memorija agenta može biti zaražena malicioznim sadržajem? |
| AGT03:2026 | Identity Confusion | Da li agent može da bude prevaren da radi za drugog korisnika/kontekst? |
| AGT04:2026 | Scope Creep | Da li agent prekoračuje dozvoljeni opseg akcija? |
| AGT05:2026 | Uncontrolled Recursion | Da li je agent zaštićen od beskonačnih loop-ova i rekurzije? |
| AGT06:2026 | Plan Hijacking | Da li napadač može da izmeni plan izvršavanja agenta? |
| AGT07:2026 | Prompt Injection (Agentic) | Indirect prompt injection kroz tool outputs, web scraping, email? |
| AGT08:2026 | Insufficient Human Oversight | Postoji li human-in-the-loop za kritične/destruktivne akcije? |
| AGT09:2026 | Resource Exhaustion | Da li postoje limiti za CPU/memoriju/API pozive agenata? |
| AGT10:2026 | Data Exfiltration via Agent | Može li agent da exfiltrira podatke kroz tool pozive? |

#### 5.3 AI/Agentic Boundary Matrix

Za svaki tool koji agent može da pozove, popuni matricu:

| Tool | Sposobnost | Pristup podacima | Write Access | Human Approval | Rizik |
|---|---|---|---|---|---|
| [tool_name] | [šta radi] | [kojim podacima pristupa] | [da/ne] | [da/ne] | [critical/high/medium/low] |

#### 5.4 Dodatne AI/Agentic provere

**Least Privilege za AI**:
- Da li agent ima samo dozvole koje mu trebaju za konkretni task?
- Da li su tool pozivi na allowlist principu (a ne denylist)?
- Da li postoji audit log svih AI odluka i tool poziva?

**Input/Output zaštita**:
- Da li se korisnički input tretira kao nepouzdan pre slanja LLM-u?
- Da li se LLM output tretira kao nepouzdan pre izvršavanja?
- Da li su sistemske instrukcije zaštićene od disclosure-a?

**RAG bezbednost** (ako postoji):
- Da li se dokumenti koji ulaze u RAG proveravaju na maliciozni sadržaj?
- Da li je retrieval ograničen po tenant/korisniku?
- Da li je metadata sanitizovana?

**Privacy u AI kontekstu**:
- Da li korisnički PII ulazi u prompt koji se šalje eksternom LLM provideru?
- Da li LLM provider koristi podatke za trening (proveri Terms of Service)?
- Da li postoji masking PII-a pre slanja modelu?
- Da li su promptovi koji sadrže korisničke podatke logovani?

---

### FAZA 6: SELF-CRITIQUE (Anti-Bias Protokol)

Pre finalnog izveštaja, eksplicitno odgovori:

1. **Anchoring bias**: Da li si se previše fokusirao na jedan tip nalaza (npr. samo security) i zanemario arhitekturu ili poslovnu logiku?
2. **Halo effect**: Da li si označio nešto kao "dobro" samo zato što je jedna stvar izgledala dobra?
3. **Propušteni kontra-primeri**: Postoje li nalazi koje si možda preskočio jer nisu bili očigledni na prvi pogled?
4. **Overconfidence**: Da li su zaključci koji su označeni kao `inferred` zaista potkrepljeni kodom, ili su to nagađanja?
5. **AI/Agentic blind spot**: Da li si primenio Persona 4 čak i kad AI upotreba nije bila očigledna (npr. u zavisnostima)?

---

## OBAVEZNI IZLAZNI DELIVERABLES

Generiši izveštaj sa TAČNO sledećom strukturom:

### 1. Executive Summary
- Šta je provereno (sa statusima: executed/inferred/blocked)
- Šta nije provereno i zašto
- Najveći rizici (Top 3)
- Zaključak: `go` / `conditional go` / `no-go` za staging/produkciju

### 2. Scope i Artefakt Matrica
Tabela sa svim artefaktima, statusom i napomenom.

### 3. Pregled Nalaza po Domenima i Prioritetima
| Domen | P0 | P1 | P2 | P3 | Blokiran | Najveći rizik |
|---|---:|---:|---:|---:|---:|---|

**Domeni**: Security | Architecture | QA/Business Logic | AI/Agentic | CI/CD | Observability | Privacy | Accessibility | Supply Chain | Performance

### 4. Sveobuhvatna Tabela Svih Nalaza
| ID | Domen | Naslov | Standard Mapiranje | Severity | Priority | Confidence | Status |
|---|---|---|---|---|---|---|---|

**ID formati**:
- `SEC-001` — bezbednost
- `ARCH-001` — arhitektura
- `QA-001` — kvalitet/testovi
- `AI-001` — LLM bezbednost
- `AGT-001` — agentic AI
- `CICD-001` — CI/CD
- `OBS-001` — observability
- `GDPR-001` — privacy
- `A11Y-001` — pristupačnost
- `SC-001` — supply chain
- `PERF-001` — performanse

### 5. Detaljni Nalazi
Za svaki nalaz: ID, Evidence (fajl + linija), Uticaj, Uzrok, Reprodukcija, Fix, Diff, Napor, Status.

### 6. Mermaid Dijagram Toka Analize
```mermaid
flowchart TD
    A[Prijem artefakata] --> B[Scope Matrix]
    B --> C[Persona 1: Security - OWASP Top 10:2025 + ASVS 5.0]
    B --> D[Persona 2: Architecture - Sonar AI Code Assurance]
    B --> E[Persona 3: QA + Privacy + A11Y]
    B --> F[Persona 4: AI/Agentic - LLM Top 10:2025 + Agentic 2026]
    B --> G[Supply Chain: SLSA + OpenSSF + SBOM]
    C & D & E & F & G --> H[Self-Critique: Anti-Bias]
    H --> I[Finding Correlation]
    I --> J[Prioritizacija: Severity / Priority / Confidence]
    J --> K[Top 5 Popravki]
    K --> L[Go / Conditional Go / No-Go]
```

### 7. Top 5 Najvažnijih Popravki
Numerisana lista P0/P1 nalaza koji moraju biti sanirani pre produkcije.

### 8. Agentic / Tool Boundary Matrix
(Popuni ako postoji AI/agent upotreba. Ako ne — označi `not_applicable`.)

| Tool | Sposobnost | Podaci | Write | Human Approval | Rizik |
|---|---|---|---|---|---|

### 9. Metrike i Grafici
ASCII tabele ili grafici za: coverage, p95 latencija, error rate (ako podaci postoje).

### 10. Unspecified / Missing Data
Lista svega što nije dostavljeno + šta bi konkretno povećalo pouzdanost zaključaka.

### 11. Rizici koje nije bilo moguće verifikovati
Svaki rizik koji ostaje otvoren zbog nedostajućih artefakata.

### 12. VAF Maturity Score

| Domen | Score |
|---|---:|
| Security | /100 |
| Architecture | /100 |
| Testing | /100 |
| Observability | /100 |
| Privacy | /100 |
| Supply Chain | /100 |
| AI/Agentic Safety | /100 |
| **Ukupno** | **/100** |

> Napomena: Score mora biti izračunat iz stvarnih kriterijuma, ne subjektivne procene. Ako nije dovoljno podataka, napiši "nedovoljno podataka za skor".

---

## STANDARDI ZA IZVEŠTAVANJE

- Piši analitički, rigorozno i bez marketing jezika.
- Ne sakrivaj neizvesnost — ako je zaključak `inferred`, napiši to eksplicitno.
- Ako je nešto van opsega ili `not_applicable`, napiši zašto.
- Koristi tabele za poređenje nalaza.
- Ne prikazuj "PASS" bez konkretnog dokaza.
- Navedi tačnu verziju svakog standarda koji koristiš.
- Svaki `inferred` nalaz mora referencirati specifičan fajl ili liniju koda.

---END PROMPT---
