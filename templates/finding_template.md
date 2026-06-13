# Šablon: Detaljan Nalaz
# Kopirajte i popunite za svaki identifikovani nalaz tokom analize

---

## [ID: DOMEN-NNN] — [Kratki naslov nalaza]

> **Format ID-a**: `SEC-001`, `PERF-003`, `ARCH-002`, `A11Y-001`, `CICD-004`, `OBS-002`, `GDPR-001`, `QA-003`

---

### Metapodaci

| Polje | Vrednost |
|---|---|
| **ID** | [npr. SEC-001] |
| **Domen** | [Bezbednost / Performanse / Arhitektura / QA / CI/CD / Observability / GDPR / UX+A11y / Troškovi] |
| **Naslov** | [Action-oriented naslov, npr. "Hardkodovani API ključ u auth modulu"] |
| **OWASP Mapiranje** | [npr. A05:2025 – Injection; API5:2023 – BFLA; ili N/A] |
| **Severity** | [Critical / High / Medium / Low / Info] |
| **Priority** | [P0 / P1 / P2 / P3] |
| **Confidence** | [High / Medium / Low] |
| **Status** | [executed / inferred / blocked / not_applicable] |
| **Procena napora** | [S – manje od 2h / M – 2h do 1 dan / L – više od 1 dana] |

---

### Opis

[Kratak, precizan opis nalaza u 2–4 rečenice. Šta je problem? Gdje je lociran u kodu?]

---

### Dokaz / Evidence

```
[Konkretan dokaz: fajl + linija koda, log excerpt, metrika, komanda i njen izlaz]
```

Primjer format:
```
Fajl: src/auth/login.py, linija 47
Log: 2025-06-13 14:30:01 ERROR [auth] Unhandled exception: NullReferenceException
Metrika: p95 latencija = 1240ms (cilj: <300ms)
```

---

### Uticaj na Korisnika i Biznis

[Konkretno: što znači ovaj nalaz za krajnjeg korisnika i za poslovni rizik organizacije?]

- **Direktni uticaj na korisnika**: [npr. mogući gubitak podataka, nedostupnost servisa]
- **Poslovni rizik**: [npr. regulatorna kazna, reputacioni gubitak, finansijski gubitak]
- **Uticaj na produkciju**: [Kritično / Visoko / Srednje / Nisko]

---

### Tehnički Uzrok

[Objasni zašto ovaj problem postoji. Koji arhitektonski ili implementacioni propust je doveo do ovoga?]

Tipični uzroci u vibe-kodiranim aplikacijama:
- [ ] AI optimizovao za brzinu, zanemario sanitizaciju
- [ ] Nedostatak threat modelinga u dizajn fazi
- [ ] Nema peer review — AI izlaz prihvaćen kao finalan
- [ ] Halucinovana zavisnost ubačena bez provere
- [ ] Error handling sveden na prazan catch blok

---

### Koraci za Reprodukciju

1. [Korak 1]
2. [Korak 2]
3. [Korak 3 — očekivani vs. stvarni rezultat]

```bash
# Primjer komande za reprodukciju:
curl -X GET "https://api.example.com/admin/users" \
  -H "Authorization: Bearer <bilo-koji-token>"
# Očekivano: 403 Forbidden
# Stvarno: 200 OK — lista svih korisnika
```

---

### Preporuka za Popravku

[Precizna preporuka sa konkretnim tehničkim pristupom. Šta tačno treba uraditi?]

---

### Kod Primer ili Diff-Smernica

```diff
# Primjer diff-a za popravku:
- # Loš obrazac (vibe-kodirano)
- query = "SELECT * FROM users WHERE id = " + user_id

+ # Ispravan obrazac (parametrizovan upit)
+ query = "SELECT * FROM users WHERE id = %s"
+ cursor.execute(query, (user_id,))
```

---

### Šta Je Potrebno da bi se Nalaz Potpuno Verifikovao

[Ako su podaci nepotpuni ili je status `inferred` / `blocked`, navedite šta konkretno treba da se dostavi:]

- [ ] Runtime logovi za period [datum]–[datum]
- [ ] Pristup staging okruženju za reprodukciju
- [ ] Tracing data za endpoint X
- [ ] SAST scan izveštaj (Trivy/Bandit JSON output)

---

### Vezani Nalazi

- [ID drugog nalaza koji je vezan ili uzrokuje ovaj nalaz]
- [npr. CICD-002 — bez quality gate-a ovaj SEC-001 ne bi bio blokiran pre merge-a]
