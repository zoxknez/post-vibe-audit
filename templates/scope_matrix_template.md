# Šablon: Scope & Artefakt Matrica
# Kopirajte i popunite prije pokretanja analize

## Osnovna identifikacija

- **Naziv projekta**: [naziv]
- **Datum analize**: [YYYY-MM-DD]
- **Analiticar / Tim**: [ime]
- **Vremenski okvir**: [ ] Brza provera (1-2h)  [ ] Dubinska analiza (1-3 dana)
- **Ciljno okruženje za analizu**: [ ] Dev  [ ] Staging  [ ] Production

---

## Artefakt Matrica

| # | Kategorija artefakta | Šta je potrebno | Status | Lokacija / Napomena |
|---|---|---|---|---|
| 1 | **Repo i verzija** | URL ili putanja do repozitorijuma | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 2 | **Branch i commit** | Branch name, commit SHA, tag | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 3 | **Build artefakti** | Izlazi CI build-a, release packages | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 4 | **Docker / Container** | Dockerfile, image referenca | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 5 | **SBOM** | Software Bill of Materials, artifact attestation | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 6 | **CI/CD konfiguracije** | `.github/workflows/`, `.gitlab-ci.yml`, ostali pipeline fajlovi | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 7 | **IaC fajlovi** | Helm charts, Kustomize, Terraform, Ansible, K8s manifesti | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 8 | **Dependency manifests** | `package.json`, `pyproject.toml`, `requirements.txt`, lock fajlovi | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 9 | **Env inventar (redaktovan)** | Nazivi varijabli, opis namene, maskirane vrednosti, lokacija (CI/vault) | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 10 | **Feature flags** | Lista feature flag-ova po okruženjima | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 11 | **Logovi aplikacije** | Application logs (staging/prod) | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 12 | **Infrastructuralni logovi** | Server, proxy, cloud provider logs | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 13 | **Crash dump-ovi / Error reports** | Crash reports, Sentry export, core dumps | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 14 | **Metrike i dashboardi** | Prometheus/Grafana eksport, CloudWatch metrike | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 15 | **Tracing podaci** | Distributed traces (Jaeger, Tempo, DataDog) | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 16 | **Alert pravila** | Alertmanager rules, SLO/SLA definicije | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 17 | **Unit / Integration testovi** | Test suite sa rezultatima (JUnit XML, pytest XML) | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 18 | **E2E testovi** | End-to-end test suite (Playwright, Cypress) | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 19 | **Coverage izveštaji** | HTML/XML/JSON coverage report | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 20 | **Lint konfiguracija i izveštaji** | ESLint config, SonarQube scan rezultati, Bandit output | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 21 | **SAST / DAST izveštaji** | ZAP report, Trivy output, Bandit JSON | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 22 | **API specifikacija** | OpenAPI/Swagger, GraphQL schema, SOAP WSDL, Postman kolekcija | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 23 | **DB schema i migracije** | SQL schema, ORM modeli, Alembic/Flyway migracije | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 24 | **Indeksni plan i spori upiti** | EXPLAIN output, slow query log | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 25 | **Load / Stress rezultati** | Locust HTML/JSON, JMeter HTML dashboard, p95/p99 metrike | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 26 | **Arhitekturni dijagrami** | C4 dijagrami, sequence dijagrami, ER dijagrami | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 27 | **ADR-ovi** | Architecture Decision Records iz `.vibe_audit/adrs/` | ⬜ available / ⬜ partial / ⬜ unspecified | |
| 28 | **README i runbook-ovi** | Operativna dokumentacija, runbook-ovi, playbook-ovi | ⬜ available / ⬜ partial / ⬜ unspecified | |

---

## Opseg Analize

Označi koje dimenzije su u opsegu za ovu analizu:

- [ ] Funkcionalna ispravnost
- [ ] Bezbednost (OWASP Top 10:2025 + API Security Top 10:2023)
- [ ] Performanse i skalabilnost
- [ ] Stabilnost i pouzdanost
- [ ] Arhitektura i dizajn
- [ ] Kvalitet koda (SonarQube "Sonar way for AI Code")
- [ ] CI/CD i deployment konfiguracije
- [ ] Observability (logovi, metrike, tracing, alerting)
- [ ] Privatnost i usklađenost (GDPR Čl.25/30/32)
- [ ] UX i pristupačnost (WCAG 2.2 AA)
- [ ] Troškovi i optimizacija resursa

---

## Stack informacije

Popunite da biste omogućili alate prilagođene stack-u:

- **Backend jezik(ci)**: [Python / Node.js / Java / Go / Rust / C# / ...]
- **Frontend framework**: [React / Vue / Angular / Next.js / Svelte / ...]
- **Baza podataka**: [PostgreSQL / MySQL / MongoDB / Redis / ...]
- **Deployment target**: [AWS / Azure / GCP / On-premise / Docker / K8s / ...]
- **CI/CD platforma**: [GitHub Actions / GitLab CI / Jenkins / CircleCI / ...]
- **Monitoring stack**: [Prometheus+Grafana / DataDog / NewRelic / CloudWatch / ...]
- **API tip**: [REST / GraphQL / gRPC / WebSocket / ...]
- **Auth mehanizam**: [JWT / OAuth2 / SAML / API Key / Session / ...]
