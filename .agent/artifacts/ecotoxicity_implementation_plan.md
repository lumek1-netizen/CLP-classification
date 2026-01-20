# Implementační plán: Podpora ekotoxických parametrů (LC50/LD50/EC50)

**Vytvořeno:** 2026-01-20  
**Projekt:** CLP_Calculator  
**Cíl:** Doplnění podpory pro LC50, LD50, EC50 a související ekotoxické parametry v souladu s nařízením CLP (ES) č. 1272/2008 – Třída 4.1 (Nebezpečnost pro vodní prostředí)

---

## 📋 Executive Summary

Aktuálně aplikace CLP_Calculator **nepodporuje zadávání a zpracování ekotoxických parametrů** (LC50, LD50, EC50), které jsou **povinné** pro správnou klasifikaci směsí dle **Přílohy I, část 4.1 nařízení CLP**. Tento implementační plán navrhuje **postupné rozšíření datového modelu, UI, výpočetní logiky a validace** tak, aby aplikace splňovala požadavky na ekotoxicitu, aniž by došlo k narušení stávající funkcionality.

---

## 🎯 Rozsah implementace

### ✅ Implementovány budou:
1. **Datový model** – přidání polí pro LC50, LD50, EC50 do tabulky `Substance`
2. **Databázové migrace** – Alembic migrace pro nová pole
3. **UI formuláře** – rozšíření `substance_form.html` o sekci ekotoxických parametrů
4. **Validace** – kontrola rozsahů, jednotek a logické konzistence dat
5. **Výpočetní logika** – rozšíření `app/services/clp/env.py` o klasifikaci na základě LC50/EC50
6. **Zobrazení výsledků** – indikace v `substance_detail.html` a `mixture_detail.html`
7. **Testy** – unit testy pro novou funkcionalitu
8. **Dokumentace** – aktualizace README a inline dokumentace

### ❌ Neměněny zůstanou:
- Stávající výpočetní logika pro akutní toxicitu (ATE)
- Logika pro M-faktory a SCL
- Fyzikální nebezpečnost (Flammable Liquids, atd.)
- Zdravotní nebezpečnost (Skin Corrosion, atd.)
- Navigace, autentizace, audit log
- Export/import funkcionalita

---

## 📐 Architektura řešení

```
┌─────────────────────────────────────────────────────────────┐
│                    DATOVÝ MODEL                              │
│   Substance.lc50_air (float)    - LC50 pro inhalaci (mg/m³) │
│   Substance.lc50_water (float)  - LC50 pro vodní org. (mg/L)│
│   Substance.ec50_water (float)  - EC50 pro vodní org. (mg/L)│
│   Substance.ld50_oral (float)   - LD50 orální (mg/kg)       │
│   Substance.ld50_dermal (float) - LD50 dermální (mg/kg)     │
│   Substance.exposure_duration (int) - Doba expozice (h)     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  VÝPOČETNÍ LOGIKA                            │
│   app/services/clp/ecotoxicity.py (NOVÝ MODUL)              │
│   - classify_ecotoxicity()                                   │
│   - assign_aquatic_acute_category()                          │
│   - assign_aquatic_chronic_category()                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  UI A ZOBRAZENÍ                              │
│   templates/substance_form.html - Sekce "Ekotoxicita"       │
│   templates/substance_detail.html - Zobrazení LC50/EC50     │
│   templates/mixture_detail.html - Klasifikace aquatic       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔢 Fáze implementace

### **FÁZE 1: Rozšíření datového modelu a migrace**
**Cíl:** Přidat databázové sloupce pro ekotoxické parametry.

#### **Krok 1.1: Rozšířit `app/models/substance.py`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\app\models\substance.py`

**Přidat pole:**
```python
# Ekotoxické parametry (pro klasifikaci dle 4.1 CLP)
lc50_air = db.Column(db.Float, nullable=True)  # mg/m³ (inhalace)
lc50_water = db.Column(db.Float, nullable=True)  # mg/L (vodní organismy)
ec50_water = db.Column(db.Float, nullable=True)  # mg/L (vodní organismy)
ld50_oral = db.Column(db.Float, nullable=True)  # mg/kg (orální toxicita)
ld50_dermal = db.Column(db.Float, nullable=True)  # mg/kg (dermální toxicita)
exposure_duration = db.Column(db.Integer, nullable=True)  # hodiny (24h, 48h, 96h)
```

**Rozšířit `__table_args__`:**
```python
db.CheckConstraint("lc50_air >= 0 OR lc50_air IS NULL", name="check_lc50_air_positive"),
db.CheckConstraint("lc50_water >= 0 OR lc50_water IS NULL", name="check_lc50_water_positive"),
db.CheckConstraint("ec50_water >= 0 OR ec50_water IS NULL", name="check_ec50_water_positive"),
db.CheckConstraint("ld50_oral >= 0 OR ld50_oral IS NULL", name="check_ld50_oral_positive"),
db.CheckConstraint("ld50_dermal >= 0 OR ld50_dermal IS NULL", name="check_ld50_dermal_positive"),
db.CheckConstraint("exposure_duration IN (24, 48, 72, 96) OR exposure_duration IS NULL", name="check_exposure_duration_valid"),
```

**Rozšířit `to_dict()`:**
```python
"lc50_air": self.lc50_air,
"lc50_water": self.lc50_water,
"ec50_water": self.ec50_water,
"ld50_oral": self.ld50_oral,
"ld50_dermal": self.ld50_dermal,
"exposure_duration": self.exposure_duration,
```

---

#### **Krok 1.2: Vytvořit Alembic migraci**
**Příkaz:**
```powershell
venv\Scripts\activate
python -m flask db migrate -m "Add ecotoxicity parameters to Substance model"
python -m flask db upgrade
```

**Ověření:**
```powershell
python -m flask db current
```

---

### **FÁZE 2: Rozšíření formulářů a validace**
**Cíl:** Umožnit uživatelům zadávat ekotoxické parametry.

#### **Krok 2.1: Rozšířit `app/forms/substance.py`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\app\forms\substance.py`

**Přidat pole:**
```python
from wtforms.validators import NumberRange, Optional

# Ekotoxické parametry
lc50_air = FloatField(
    'LC50 (vzduch, mg/m³)',
    validators=[Optional(), NumberRange(min=0, message="Hodnota musí být nezáporná")]
)
lc50_water = FloatField(
    'LC50 (voda, mg/L)',
    validators=[Optional(), NumberRange(min=0, message="Hodnota musí být nezáporná")]
)
ec50_water = FloatField(
    'EC50 (voda, mg/L)',
    validators=[Optional(), NumberRange(min=0, message="Hodnota musí být nezáporná")]
)
ld50_oral = FloatField(
    'LD50 (orální, mg/kg)',
    validators=[Optional(), NumberRange(min=0, message="Hodnota musí být nezáporná")]
)
ld50_dermal = FloatField(
    'LD50 (dermální, mg/kg)',
    validators=[Optional(), NumberRange(min=0, message="Hodnota musí být nezáporná")]
)
exposure_duration = SelectField(
    'Doba expozice (h)',
    choices=[('', '-- Vyberte --'), ('24', '24h'), ('48', '48h'), ('72', '72h'), ('96', '96h')],
    validators=[Optional()],
    coerce=lambda x: int(x) if x else None
)
```

---

#### **Krok 2.2: Rozšířit `templates/substance_form.html`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\templates\substance_form.html`

**Přidat novou sekci po "M-faktory":**
```html
<!-- Sekce: Ekotoxické parametry (CLP 4.1) -->
<div class="category-section">
    <h3>🌊 Ekotoxické parametry (Třída 4.1 - Vodní prostředí)</h3>
    <p class="info-text">
        Parametry pro klasifikaci akutní a chronické toxicity pro vodní organismy podle Přílohy I, část 4.1 nařízení CLP.
        <span class="tooltip">ⓘ
            <span class="tooltiptext">
                <strong>LC50:</strong> Letální koncentrace 50% (mortality)<br>
                <strong>EC50:</strong> Efektivní koncentrace 50% (sub-lethal effects)<br>
                <strong>LD50:</strong> Letální dávka 50% (oral/dermal)
            </span>
        </span>
    </p>
    
    <div class="form-grid three-column">
        <!-- LC50 (vzduch) -->
        <div class="form-group">
            {{ form.lc50_air.label }}
            {{ form.lc50_air(class="form-control", placeholder="0.00") }}
            {% if form.lc50_air.errors %}
                <div class="error">{{ form.lc50_air.errors[0] }}</div>
            {% endif %}
        </div>
        
        <!-- LC50 (voda) -->
        <div class="form-group">
            {{ form.lc50_water.label }}
            {{ form.lc50_water(class="form-control", placeholder="0.00") }}
            {% if form.lc50_water.errors %}
                <div class="error">{{ form.lc50_water.errors[0] }}</div>
            {% endif %}
        </div>
        
        <!-- EC50 (voda) -->
        <div class="form-group">
            {{ form.ec50_water.label }}
            {{ form.ec50_water(class="form-control", placeholder="0.00") }}
            {% if form.ec50_water.errors %}
                <div class="error">{{ form.ec50_water.errors[0] }}</div>
            {% endif %}
        </div>
        
        <!-- LD50 (orální) -->
        <div class="form-group">
            {{ form.ld50_oral.label }}
            {{ form.ld50_oral(class="form-control", placeholder="0.00") }}
            {% if form.ld50_oral.errors %}
                <div class="error">{{ form.ld50_oral.errors[0] }}</div>
            {% endif %}
        </div>
        
        <!-- LD50 (dermální) -->
        <div class="form-group">
            {{ form.ld50_dermal.label }}
            {{ form.ld50_dermal(class="form-control", placeholder="0.00") }}
            {% if form.ld50_dermal.errors %}
                <div class="error">{{ form.ld50_dermal.errors[0] }}</div>
            {% endif %}
        </div>
        
        <!-- Doba expozice -->
        <div class="form-group">
            {{ form.exposure_duration.label }}
            {{ form.exposure_duration(class="form-control") }}
            {% if form.exposure_duration.errors %}
                <div class="error">{{ form.exposure_duration.errors[0] }}</div>
            {% endif %}
        </div>
    </div>
</div>
```

**Styl (v `static/style.css`):**
```css
.form-grid.three-column {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
}

@media (max-width: 768px) {
    .form-grid.three-column {
        grid-template-columns: 1fr;
    }
}
```

---

#### **Krok 2.3: Aktualizovat `app/routes/substances.py`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\app\routes\substances.py`

**V části `create_substance()` a `edit_substance()` – přidat mapování:**
```python
substance.lc50_air = form.lc50_air.data
substance.lc50_water = form.lc50_water.data
substance.ec50_water = form.ec50_water.data
substance.ld50_oral = form.ld50_oral.data
substance.ld50_dermal = form.ld50_dermal.data
substance.exposure_duration = form.exposure_duration.data
```

---

### **FÁZE 3: Implementace výpočetní logiky**
**Cíl:** Klasifikovat směsi na základě LC50/EC50 hodnot.

#### **Krok 3.1: Vytvořit `app/services/clp/ecotoxicity.py`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\app\services\clp\ecotoxicity.py` (NOVÝ)

**Obsah:**
```python
"""
Modul pro klasifikaci ekotoxicity podle Přílohy I, část 4.1 nařízení CLP.
Implementuje klasifikaci na základě LC50, EC50 a LD50 hodnot.
"""

from typing import Optional, Tuple


def assign_aquatic_acute_category(lc50: Optional[float], ec50: Optional[float]) -> Optional[int]:
    """
    Přiřadí kategorii Aquatic Acute na základě LC50/EC50.
    
    Kritéria (Příloha I, tabulka 4.1.0):
    - Kategorie 1: LC50/EC50 ≤ 1 mg/L
    
    Args:
        lc50: LC50 hodnota v mg/L
        ec50: EC50 hodnota v mg/L
        
    Returns:
        1 pro Aquatic Acute 1, None pokud nekritéria nesplněna
    """
    effective_value = None
    
    # Použij nejnižší dostupnou hodnotu (nejkonzervativnější přístup)
    if lc50 is not None and ec50 is not None:
        effective_value = min(lc50, ec50)
    elif lc50 is not None:
        effective_value = lc50
    elif ec50 is not None:
        effective_value = ec50
    
    if effective_value is None:
        return None
    
    if effective_value <= 1.0:
        return 1
    
    return None


def assign_aquatic_chronic_category(
    lc50: Optional[float],
    ec50: Optional[float],
    is_rapidly_degradable: bool = False,
    noec: Optional[float] = None
) -> Optional[int]:
    """
    Přiřadí kategorii Aquatic Chronic na základě LC50/EC50 a dalších faktorů.
    
    Kritéria (Příloha I, tabulka 4.1.0):
    - Kategorie 1: LC50/EC50 ≤ 1 mg/L a není rychle rozložitelná
    - Kategorie 2: 1 < LC50/EC50 ≤ 10 mg/L a není rychle rozložitelná
    - Kategorie 3: 10 < LC50/EC50 ≤ 100 mg/L a není rychle rozložitelná
    - Kategorie 4: Způsobí dlouhodobé účinky (NOEC < 1 mg/L nebo chybí data)
    
    Args:
        lc50: LC50 hodnota v mg/L
        ec50: EC50 hodnota v mg/L
        is_rapidly_degradable: Je látka rychle rozložitelná?
        noec: No Observed Effect Concentration (mg/L)
        
    Returns:
        1-4 pro Aquatic Chronic 1-4, None pokud kritéria nesplněna
    """
    effective_value = None
    
    if lc50 is not None and ec50 is not None:
        effective_value = min(lc50, ec50)
    elif lc50 is not None:
        effective_value = lc50
    elif ec50 is not None:
        effective_value = ec50
    
    if effective_value is None:
        return None
    
    # Kategorie 1: <= 1 mg/L a není rychle rozložitelná
    if effective_value <= 1.0 and not is_rapidly_degradable:
        return 1
    
    # Kategorie 2: 1 < x <= 10 mg/L a není rychle rozložitelná
    if 1.0 < effective_value <= 10.0 and not is_rapidly_degradable:
        return 2
    
    # Kategorie 3: 10 < x <= 100 mg/L a není rychle rozložitelná
    if 10.0 < effective_value <= 100.0 and not is_rapidly_degradable:
        return 3
    
    # Kategorie 4: Dlouhodobé účinky (NOEC < 1 mg/L nebo chybí data)
    if noec is not None and noec < 1.0:
        return 4
    
    return None


def get_h_code_from_ecotoxicity(
    acute_category: Optional[int],
    chronic_category: Optional[int]
) -> Tuple[set, set]:
    """
    Převede kategorie ekotoxicity na H-kódy a GHS piktogramy.
    
    Args:
        acute_category: Aquatic Acute kategorie (1 nebo None)
        chronic_category: Aquatic Chronic kategorie (1-4 nebo None)
        
    Returns:
        (set of H-codes, set of GHS codes)
    """
    h_codes = set()
    ghs_codes = set()
    
    if acute_category == 1:
        h_codes.add("H400")
        ghs_codes.add("GHS09")
    
    if chronic_category == 1:
        h_codes.add("H410")
        ghs_codes.add("GHS09")
    elif chronic_category == 2:
        h_codes.add("H411")
        ghs_codes.add("GHS09")
    elif chronic_category == 3:
        h_codes.add("H412")
    elif chronic_category == 4:
        h_codes.add("H413")
    
    return h_codes, ghs_codes
```

---

#### **Krok 3.2: Integrovat do `app/services/clp/env.py`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\app\services\clp\env.py`

**Přidat import:**
```python
from .ecotoxicity import (
    assign_aquatic_acute_category,
    assign_aquatic_chronic_category,
    get_h_code_from_ecotoxicity
)
```

**V `classify_environmental_hazards()` – přidat před iteraci `for component in mixture.components:`:**
```python
# NOVÁ LOGIKA: Klasifikace na základě LC50/EC50
for component in mixture.components:
    substance = component.substance
    concentration = component.concentration
    sub_name = substance.name
    
    # Zkontroluj, zda má látka ekotoxická data
    if substance.lc50_water or substance.ec50_water:
        acute_cat = assign_aquatic_acute_category(substance.lc50_water, substance.ec50_water)
        chronic_cat = assign_aquatic_chronic_category(
            substance.lc50_water,
            substance.ec50_water,
            is_rapidly_degradable=False  # TODO: Přidat pole do DB
        )
        
        if acute_cat:
            h_codes, ghs = get_h_code_from_ecotoxicity(acute_cat, None)
            env_hazards.update(h_codes)
            env_ghs.update(ghs)
            log_entries.append({
                "step": "Ekotoxicita (LC50/EC50)",
                "detail": f"{sub_name}: Aquatic Acute {acute_cat} (LC50={substance.lc50_water or 'N/A'}, EC50={substance.ec50_water or 'N/A'})",
                "result": list(h_codes)[0]
            })
        
        if chronic_cat:
            h_codes, ghs = get_h_code_from_ecotoxicity(None, chronic_cat)
            env_hazards.update(h_codes)
            env_ghs.update(ghs)
            log_entries.append({
                "step": "Ekotoxicita (Chronická)",
                "detail": f"{sub_name}: Aquatic Chronic {chronic_cat}",
                "result": list(h_codes)[0]
            })
```

---

### **FÁZE 4: Testování**
**Cíl:** Ověřit správnost implementace.

#### **Krok 4.1: Vytvořit `tests/test_ecotoxicity.py`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\tests\test_ecotoxicity.py` (NOVÝ)

**Obsah:**
```python
"""Test klasifikace ekotoxicity podle LC50/EC50."""

import pytest
from app.services.clp.ecotoxicity import (
    assign_aquatic_acute_category,
    assign_aquatic_chronic_category,
    get_h_code_from_ecotoxicity
)


class TestAquaticAcuteClassification:
    """Testy pro Aquatic Acute kategorizaci."""
    
    def test_acute_cat1_lc50(self):
        """LC50 <= 1 mg/L -> Kategorie 1"""
        assert assign_aquatic_acute_category(lc50=0.5, ec50=None) == 1
    
    def test_acute_cat1_ec50(self):
        """EC50 <= 1 mg/L -> Kategorie 1"""
        assert assign_aquatic_acute_category(lc50=None, ec50=0.8) == 1
    
    def test_acute_cat1_both(self):
        """Min(LC50, EC50) <= 1 mg/L -> Kategorie 1"""
        assert assign_aquatic_acute_category(lc50=0.5, ec50=0.3) == 1
    
    def test_acute_no_category(self):
        """LC50 > 1 mg/L -> Žádná kategorie"""
        assert assign_aquatic_acute_category(lc50=5.0, ec50=None) is None
    
    def test_acute_no_data(self):
        """Žádná data -> Žádná kategorie"""
        assert assign_aquatic_acute_category(lc50=None, ec50=None) is None


class TestAquaticChronicClassification:
    """Testy pro Aquatic Chronic kategorizaci."""
    
    def test_chronic_cat1(self):
        """LC50 <= 1 mg/L, není rychle rozložitelná -> Kategorie 1"""
        assert assign_aquatic_chronic_category(lc50=0.5, ec50=None, is_rapidly_degradable=False) == 1
    
    def test_chronic_cat2(self):
        """1 < LC50 <= 10 mg/L -> Kategorie 2"""
        assert assign_aquatic_chronic_category(lc50=5.0, ec50=None, is_rapidly_degradable=False) == 2
    
    def test_chronic_cat3(self):
        """10 < LC50 <= 100 mg/L -> Kategorie 3"""
        assert assign_aquatic_chronic_category(lc50=50.0, ec50=None, is_rapidly_degradable=False) == 3
    
    def test_chronic_cat4_noec(self):
        """NOEC < 1 mg/L -> Kategorie 4"""
        assert assign_aquatic_chronic_category(lc50=200.0, ec50=None, noec=0.5) == 4
    
    def test_chronic_rapidly_degradable(self):
        """Rychle rozložitelná -> nižší kategorie nebo žádná"""
        # Pro rychle rozložitelné látky platí jiná kritéria
        result = assign_aquatic_chronic_category(lc50=0.5, ec50=None, is_rapidly_degradable=True)
        assert result is None  # V aktuální implementaci


class TestHCodeAssignment:
    """Testy pro přiřazení H-kódů."""
    
    def test_acute_h400(self):
        """Acute Cat 1 -> H400 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=1, chronic_category=None)
        assert "H400" in h_codes
        assert "GHS09" in ghs
    
    def test_chronic_h410(self):
        """Chronic Cat 1 -> H410 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=1)
        assert "H410" in h_codes
        assert "GHS09" in ghs
    
    def test_chronic_h411(self):
        """Chronic Cat 2 -> H411 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=2)
        assert "H411" in h_codes
        assert "GHS09" in ghs
    
    def test_chronic_h412(self):
        """Chronic Cat 3 -> H412 (bez GHS09)"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=3)
        assert "H412" in h_codes
    
    def test_chronic_h413(self):
        """Chronic Cat 4 -> H413"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=4)
        assert "H413" in h_codes
```

**Spustit testy:**
```powershell
pytest tests/test_ecotoxicity.py -v
```

---

### **FÁZE 5: Zobrazení v UI**
**Cíl:** Zobrazit ekotoxické parametry v detailech látek a směsí.

#### **Krok 5.1: Aktualizovat `templates/substance_detail.html`**
**Přidat po sekci ATE hodnot:**
```html
<!-- Ekotoxické parametry -->
{% if substance.lc50_air or substance.lc50_water or substance.ec50_water or substance.ld50_oral or substance.ld50_dermal %}
<div class="detail-section">
    <h3>🌊 Ekotoxické parametry</h3>
    <table class="detail-table">
        {% if substance.lc50_air %}
        <tr>
            <th>LC50 (vzduch):</th>
            <td>{{ substance.lc50_air }} mg/m³</td>
        </tr>
        {% endif %}
        {% if substance.lc50_water %}
        <tr>
            <th>LC50 (voda):</th>
            <td>{{ substance.lc50_water }} mg/L</td>
        </tr>
        {% endif %}
        {% if substance.ec50_water %}
        <tr>
            <th>EC50 (voda):</th>
            <td>{{ substance.ec50_water }} mg/L</td>
        </tr>
        {% endif %}
        {% if substance.ld50_oral %}
        <tr>
            <th>LD50 (orální):</th>
            <td>{{ substance.ld50_oral }} mg/kg</td>
        </tr>
        {% endif %}
        {% if substance.ld50_dermal %}
        <tr>
            <th>LD50 (dermální):</th>
            <td>{{ substance.ld50_dermal }} mg/kg</td>
        </tr>
        {% endif %}
        {% if substance.exposure_duration %}
        <tr>
            <th>Doba expozice:</th>
            <td>{{ substance.exposure_duration }} hodin</td>
        </tr>
        {% endif %}
    </table>
</div>
{% endif %}
```

---

### **FÁZE 6: Dokumentace**
**Cíl:** Dokumentovat novou funkcionalitu.

#### **Krok 6.1: Aktualizovat `README.md`**
**Přidat do sekce "Funkce aplikace":**
```markdown
### 🌊 Ekotoxické parametry
- **LC50/EC50/LD50**: Zadávání a klasifikace na základě letálních a efektivních koncentrací
- **Aquatic Acute/Chronic**: Automatické přiřazení kategorií 1-4 dle Přílohy I, část 4.1
- **Doba expozice**: Podpora standardních dob testování (24h, 48h, 72h, 96h)
```

#### **Krok 6.2: Vytvořit `docs/ecotoxicity_guide.md`**
**Soubor:** `c:\Users\lumek\Projects\CLP_Calculator\docs\ecotoxicity_guide.md` (NOVÝ)

**Obsah:**
```markdown
# Průvodce ekotoxicitou v CLP_Calculator

## Úvod
Tento dokument popisuje, jak aplikace CLP_Calculator zpracovává ekotoxické parametry 
a klasifikuje látky/směsi dle Přílohy I, část 4.1 nařízení CLP.

## Podporované parametry
1. **LC50 (Lethal Concentration 50%)**
   - LC50 (vzduch): Pro inhalační toxicitu (mg/m³)
   - LC50 (voda): Pro vodní organismy (mg/L)

2. **EC50 (Effective Concentration 50%)**
   - EC50 (voda): Sub-letální účinky na vodní organismy (mg/L)

3. **LD50 (Lethal Dose 50%)**
   - LD50 (orální): Perorální toxicita (mg/kg)
   - LD50 (dermální): Dermální toxicita (mg/kg)

## Klasifikační kritéria

### Aquatic Acute (Akutní toxicita pro vodní prostředí)
| Kategorie | Kritérium (LC50/EC50) | H-kód | GHS |
|-----------|----------------------|-------|-----|
| Aquatic Acute 1 | ≤ 1 mg/L | H400 | GHS09 |

### Aquatic Chronic (Chronická toxicita pro vodní prostředí)
| Kategorie | Kritérium (není rychle rozložitelná) | H-kód | GHS |
|-----------|--------------------------------------|-------|-----|
| Aquatic Chronic 1 | ≤ 1 mg/L | H410 | GHS09 |
| Aquatic Chronic 2 | 1 < x ≤ 10 mg/L | H411 | GHS09 |
| Aquatic Chronic 3 | 10 < x ≤ 100 mg/L | H412 | - |
| Aquatic Chronic 4 | NOEC < 1 mg/L nebo chybí data | H413 | - |

## Příklad použití
1. Otevřete formulář látky
2. Zadejte LC50 (voda) = 0.5 mg/L
3. Uložte látku
4. Přidejte látku do směsi (např. 10%)
5. Klasifikace směsi automaticky přiřadí H400 (Aquatic Acute 1)

## Reference
- Nařízení (ES) č. 1272/2008 (CLP), Příloha I, část 4.1
- ECHA Guidance on the Application of the CLP Criteria, verze 5.0
```

---

## ✅ Kontrolní seznam (Checklist)

### Fáze 1: Datový model
- [ ] Přidána pole `lc50_air`, `lc50_water`, `ec50_water`, `ld50_oral`, `ld50_dermal`, `exposure_duration` do `Substance`
- [ ] Přidány `CheckConstraint` pro validaci nezáporných hodnot
- [ ] Rozšířena metoda `to_dict()`
- [ ] Vytvořena Alembic migrace
- [ ] Provedena migrace databáze (`flask db upgrade`)

### Fáze 2: Formuláře
- [ ] Přidána pole do `app/forms/substance.py`
- [ ] Přidána sekce "Ekotoxické parametry" do `substance_form.html`
- [ ] Přidán CSS styl `.form-grid.three-column`
- [ ] Aktualizován `app/routes/substances.py` (mapování polí)

### Fáze 3: Výpočetní logika
- [ ] Vytvořen `app/services/clp/ecotoxicity.py`
- [ ] Implementována `assign_aquatic_acute_category()`
- [ ] Implementována `assign_aquatic_chronic_category()`
- [ ] Implementována `get_h_code_from_ecotoxicity()`
- [ ] Integrována logika do `classify_environmental_hazards()` v `env.py`

### Fáze 4: Testování
- [ ] Vytvořen `tests/test_ecotoxicity.py`
- [ ] Napsány testy pro Aquatic Acute klasifikaci
- [ ] Napsány testy pro Aquatic Chronic klasifikaci
- [ ] Napsány testy pro přiřazení H-kódů
- [ ] Všechny testy prošly (`pytest tests/test_ecotoxicity.py -v`)

### Fáze 5: UI zobrazení
- [ ] Přidána sekce ekotoxických parametrů do `substance_detail.html`
- [ ] Ověřeno zobrazení v `mixture_detail.html` (klasifikační log)

### Fáze 6: Dokumentace
- [ ] Aktualizován `README.md`
- [ ] Vytvořen `docs/ecotoxicity_guide.md`
- [ ] Přidány inline komentáře do nového kódu

---

## 🔍 Testovací scénáře

### Scénář 1: Látka s vysokou akutní toxicitou
1. Vytvořit látku "Kadmium chlorid"
2. Zadat LC50 (voda) = 0.3 mg/L
3. Přidat do směsi (15%)
4. **Očekávaný výsledek:** H400 + GHS09

### Scénář 2: Látka s chronickou toxicitou
1. Vytvořit látku "Tributyltin"
2. Zadat EC50 (voda) = 5 mg/L (není rychle rozložitelná)
3. Přidat do směsi (25%)
4. **Očekávaný výsledek:** H411 + GHS09

### Scénář 3: Kombinace více látek
1. Látka A: LC50 = 0.8 mg/L (15%)
2. Látka B: EC50 = 2.5 mg/L (10%)
3. **Očekávaný výsledek:** H400 (z látky A) + H411 (z látky B)

---

## ⚠️ Rizika a migrace strategií

### Riziko 1: Konflikty s existujícími SCL/GCL
**Popis:** Ekotoxická data mohou kolidovat s ručně zadanými SCL limity.  
**Migrace:** Přidat prioritizační logiku – ekotoxická data mají přednost před GCL.

### Riziko 2: Chybějící pole `is_rapidly_degradable`
**Popis:** Pro přesnou klasifikaci Aquatic Chronic je potřeba vědět, zda je látka rychle rozložitelná.  
**Migrace:** Přidat boolean pole `is_rapidly_degradable` do `Substance` v budoucí migraci.

### Riziko 3: Zpětná kompatibilita
**Popis:** Staré záznamy v databázi nemají ekotoxická data.  
**Migrace:** Všechna nová pole jsou `nullable=True` → žádná data loss, UI skrývá prázdné sekce.

---

## 📅 Harmonogram implementace

| Fáze | Odhadovaný čas | Priorita |
|------|----------------|----------|
| Fáze 1: Datový model | 2 hodiny | Vysoká |
| Fáze 2: Formuláře | 3 hodiny | Vysoká |
| Fáze 3: Výpočetní logika | 4 hodiny | Vysoká |
| Fáze 4: Testování | 3 hodiny | Střední |
| Fáze 5: UI zobrazení | 2 hodiny | Střední |
| Fáze 6: Dokumentace | 1 hodina | Nízká |
| **CELKEM** | **15 hodin** | - |

---

## 📚 Reference

1. **Nařízení (ES) č. 1272/2008 (CLP)**, Příloha I, část 4.1  
   - [EUR-Lex odkaz](https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:02008R1272-20231016)

2. **ECHA Guidance on the Application of the CLP Criteria**, verze 5.0  
   - [ECHA dokumenty](https://echa.europa.eu/guidance-documents/guidance-on-clp)

3. **UN GHS (Globally Harmonized System)**, Rev. 10  
   - [UNECE odkaz](https://unece.org/transport/dangerous-goods/ghs-rev10-2023)

---

## ✅ Závěr

Tento implementační plán systematicky rozšiřuje CLP_Calculator o podporu ekotoxických parametrů LC50/LD50/EC50 v souladu s nařízením CLP. Po dokončení všech fází bude aplikace plně kompatibilní s požadavky na klasifikaci nebezpečnosti pro vodní prostředí (třída 4.1).

**Doporučená strategie:** Implementovat postupně (fáze po fázi) s průběžným testováním a code review po každé fázi.
