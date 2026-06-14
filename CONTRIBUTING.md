# Contributing to Vibe-Audit Framework (VAF)

Hvala što razmišljate o doprinošenju VAF-u! Ovaj dokument objašnjava kako da doprinesete.

## Oblasti gde je doprinos najkorisniji

| Oblast | Primeri |
|---|---|
| **Novi scanner moduli** | `src/vaf/scanners/eslint.py`, `scorecard.py`, `lighthouse.py` |
| **Framework profili** | `src/vaf/profiles/nextjs.yaml`, `fastapi.yaml`, `ai-agent.yaml` |
| **Standardi** | Ažuriranje `standards/` kada izađu nove verzije OWASP/ASVS |
| **Promptovi** | Poboljšanje `prompts/pro_audit_prompt.md` |
| **Testovi i fixture projekti** | `tests/fixtures/` — novi fixture projekti sa poznatim problemima |
| **Dokumentacija** | Primeri nalaza u `examples/reports/` |

## Kako doprineti

### 1. Setup razvojnog okruženja

```bash
git clone https://github.com/zoxknez/post-vibe-audit.git
cd post-vibe-audit

# Kreirajte virtuelno okruženje
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instalirajte u dev modu
pip install -e ".[dev]"
```

### 2. Pokrenite testove

```bash
pytest tests/ -q
ruff check src/
mypy src/vaf/
```

### 3. Napravite Pull Request

- Fork repozitorijuma
- Kreirajte feature branch: `git checkout -b feature/moj-doprinos`
- Napišite testove za nove funkcionalnosti
- Pokrenite test suite — sve mora prolaziti
- Otvorite PR sa jasnim opisom šta je promenjeno i zašto

## Standardi koda

### Python kod
- **Formatiranje**: `ruff format` (konfigurisano u `pyproject.toml`)
- **Linting**: `ruff check` bez upozorenja
- **Type checking**: `mypy src/vaf/` bez grešaka
- **Docstrinzi**: Google style, na engleskom
- **Komentari u kodu**: engleski
- **Test coverage**: ≥80% za novi kod

### Promptovi i dokumentacija
- Srpski jezik (sr-Latn) za `prompts/`, `templates/`, i srpski deo `README.md`
- Engleski za `README.md` engleski deo i sve API/code docstrings

### Scanner moduli

Novi scanner modul u `src/vaf/scanners/` mora:
1. Imati `is_available() -> bool` funkciju (provera da li je alat instaliran)
2. Imati `run(path: Path, config: VAFConfig) -> ScanResult` funkciju
3. Vraćati normalizovani `ScanResult` dataclass (ne sirovi subprocess output)
4. Biti registrovan u `src/vaf/scanners/__init__.py`
5. Imati odgovarajuće testove u `tests/test_scanner_<ime>.py`

```python
# Primer skeleton-a za novi scanner
from pathlib import Path
from vaf.config import VAFConfig
from vaf.scanners.base import ScanResult

def is_available() -> bool:
    """Check if the tool is installed and accessible."""
    ...

def run(path: Path, config: VAFConfig) -> ScanResult:
    """Run the scanner and return normalized results."""
    ...
```

## Prijava grešaka

Koristite GitHub Issues sa:
- Verzijom VAF alata (`vaf --version`)
- Operativnim sistemom i verzijom Pythona
- Koracima za reprodukciju
- Očekivanim vs. stvarnim ponašanjem

## Bezbednosni propusti

**Ne koristite GitHub Issues za bezbednosne propuste!**
Pogledajte [SECURITY.md](SECURITY.md) za responsible disclosure proces.

## Licenca

Doprinošenjem, slažete se da su vaši doprinosi licencirani pod MIT licencom
(videti [LICENSE](LICENSE)).
