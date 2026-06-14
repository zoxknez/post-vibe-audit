# Security Policy — Vibe-Audit Framework (VAF)

## Podržane verzije

| Verzija | Podrška bezbednosnih zakrpa |
|---|---|
| 3.x (current) | ✅ Aktivna podrška |
| 2.x | ⚠️ Samo kritični propusti |
| < 2.0 | ❌ Bez podrške |

## Prijava bezbednosnog propusta (Responsible Disclosure)

**Molimo NE prijavljujte bezbednosne propuste putem javnih GitHub Issues.**

### Kako prijaviti

1. Pošaljite opis propusta na GitHub Security Advisories ovog repozitorijuma:
   - Idite na **Security → Advisories → Report a vulnerability**
   - Ili koristite email za privatno obelodanjivanje (videti profil maintajnera)

2. Uključite u izveštaj:
   - Opis propusta i potencijalni uticaj
   - Verziju VAF alata u kojoj ste pronašli propust
   - Korake za reprodukciju (proof-of-concept, ako je primenljivo)
   - Predlog za popravku (opciono, ali cenjeno)

### Šta da očekujete

- **Potvrda prijema**: u roku od 48 sati
- **Procena**: u roku od 7 dana
- **Zakrpa i obelodanjivanje**: koordinisano sa prijavljivačem

### Opseg

Opseg responsible disclosure pokriva:
- `src/vaf/` Python kod (CLI, packer, redaction, scanners, reporters)
- `scripts/vibe_audit_packer.py`
- GitHub Actions workflow fajlovi u `.github/workflows/`

**Van opsega**: promptovi i šabloni (`prompts/`, `templates/`) — to su tekstualni sadržaj, ne kod.

## Posebna napomena — redakcija tajni

VAF alat je dizajniran da **ne otkriva tajne**. Ako pronađete da VAF curenje tajni
(npr. `redaction.py` propušta API ključeve), to je propust visokog prioriteta
i treba da bude prijavljen putem ovog procesa.

## Zahvalnost

Zahvalni smo svim istraživačima koji odgovorno prijavljuju propuste.
Prijavljivači će biti navedeni u CHANGELOG.md (uz njihovu dozvolu).
