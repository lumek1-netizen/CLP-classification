# Průvodce ekotoxickými parametry

## 📖 Úvod

Tento dokument poskytuje podrobný návod k použití ekotoxických parametrů v CLP_Calculator pro klasifikaci nebezpečnosti pro životní prostředí podle nařízení CLP (ES) č. 1272/2008, Příloha I, část 4.1.

---

## 🎯 Co jsou ekotoxické parametry?

Ekotoxické parametry popisují **toxicitu chemických látek pro vodní organismy** a jsou klíčové pro klasifikaci environmentálních nebezpečností:

### Standardní testy

| Test | Organismus | Doba | Jednotka | Popis |
|------|-----------|------|----------|-------|
| **LC50** | Ryby (např. *Danio rerio*) | 96h | mg/L | Letální koncentrace 50% |
| **EC50** | Daphnie (*Daphnia magna*) | 48h | mg/L | Efektivní koncentrace 50% |
| **EC50** | Řasy (*Pseudokirchneriella*) | 72h | mg/L | Efektivní koncentrace 50% |
| **NOEC** | Různé organismy | Variabilní | mg/L | Koncentrace bez pozorovaného účinku |

---

## 📝 Jak zadat ekotoxická data

### Krok 1: Otevřete formulář látky

1. Přejděte na **Látky** → **Nová látka** nebo **Editovat látku**
2. Najděte sekci **🌊 Ekotoxické parametry (Třída 4.1 - Vodní prostředí)**

### Krok 2: Zadejte hodnoty testů

Formulář je rozdělen do 3 skupin:

#### 🐟 Akutní toxicita pro vodní organismy

```
┌──────────────────────────────────────────────┐
│ LC50 ryby, 96h (mg/L)     [  1.5  ]          │
│ EC50 daphnie, 48h (mg/L)  [  0.8  ]          │
│ EC50 řasy, 72h (mg/L)     [  2.3  ]          │
└──────────────────────────────────────────────┘
```

**Není nutné vyplnit všechny hodnoty** - systém použije nejnižší dostupnou hodnotu pro klasifikaci.

#### 🌱 Chronická toxicita

```
┌──────────────────────────────────────────────┐
│ NOEC (mg/L)  [  0.1  ]                       │
└──────────────────────────────────────────────┘
```

#### 🐭 Toxicita pro savce

```
┌──────────────────────────────────────────────┐
│ LD50 orální, savci (mg/kg)        [  50  ]  │
│ LD50 dermální, savci (mg/kg)      [ 100  ]  │
│ LC50 inhalace, potkani, 4h (mg/L) [ 5.0  ]  │
└──────────────────────────────────────────────┘
```

### Krok 3: Uložte látku

Systém **automaticky klasifikuje** látku na základě zadaných hodnot.

---

## 🧮 Klasifikační kritéria

### Aquatic Acute (Akutní toxicita)

| Kategorie | Kritérium | H-kód | GHS |
|-----------|-----------|-------|-----|
| **Acute 1** | min(LC50/EC50) ≤ 1 mg/L | H400 | GHS09 |

**Příklad:**
- LC50 ryby: 2.0 mg/L
- EC50 daphnie: **0.5 mg/L** ← nejnižší
- → **Aquatic Acute 1** (H400)

### Aquatic Chronic (Chronická toxicita)

> ⚠️ **Poznámka:** Následující klasifikace platí pro látky, které **NEJSOU rychle rozložitelné**.

| Kategorie | Kritérium LC50/EC50 | Kritérium NOEC | H-kód | GHS |
|-----------|---------------------|----------------|-------|-----|
| **Chronic 1** | ≤ 1 mg/L | < 0.1 mg/L | H410 | GHS09 |
| **Chronic 2** | 1–10 mg/L | 0.1–1 mg/L | H411 | GHS09 |
| **Chronic 3** | 10–100 mg/L | 1–10 mg/L | H412 | - |
| **Chronic 4** | > 100 mg/L | > 10 mg/L | H413 | - |

**Příklad 1:** Vysoká toxicita
- LC50 ryby: **0.3 mg/L**
- → **Chronic 1** (H410)

**Příklad 2:** Střední toxicita
- LC50 ryby: **15 mg/L**
- → **Chronic 3** (H412)

---

## 🔬 Praktické příklady

### Příklad 1: Síran měďnatý (CuSO₄)

**Vstupní data:**
```
LC50 (ryby, 96h):     0.30 mg/L
EC50 (daphnie, 48h):  0.18 mg/L
```

**Automatická klasifikace:**
- ✅ Aquatic Acute 1 → **H400**
- ✅ Aquatic Chronic 1 → **H410**
- ✅ GHS piktogram: **GHS09**

**Výsledek v logu směsi:**
```
Ekotoxicita (Acute 1): Síran měďnatý (5%): 
  LC50(ryby,96h)=0.3 mg/L, EC50(daphnie,48h)=0.18 mg/L

Ekotoxicita (Chronic 1): Síran měďnatý (5%): 
  LC50(ryby,96h)=0.3 mg/L, EC50(daphnie,48h)=0.18 mg/L
```

### Příklad 2: Ethanol

**Vstupní data:**
```
LC50 (ryby, 96h):  13400 mg/L
```

**Automatická klasifikace:**
- ❌ Aquatic Acute: Nesplněno (> 1 mg/L)
- ⚠️ Aquatic Chronic 4 → **H413**

### Příklad 3: Látka s částečnými daty

**Vstupní data:**
```
EC50 (daphnie, 48h):  0.75 mg/L
NOEC:                 0.05 mg/L
```

**Automatická klasifikace:**
- ✅ Aquatic Acute 1 → **H400** (EC50 ≤ 1)
- ✅ Aquatic Chronic 1 → **H410** (NOEC < 0.1)

---

## 💡 Tipy a best practices

### ✅ Co dělat

1. **Použijte oficiální data** z bezpečnostních listů nebo ECHA databáze
2. **Zadávejte všechny dostupné testy** pro přesnější klasifikaci
3. **Kontrolujte jednotky**: mg/L pro vodní testy, mg/kg pro savce
4. **Používejte standardní doby**: 96h pro ryby, 48h pro daphnie, 72h pro řasy

### ❌ Co nedělat

1. **Nemíchejte různé organismy** do jednoho pole
2. **Nezaokrouhlujte přespříliš** - používejte dostupnou přesnost
3. **Nepřeskakujte validaci** - kontrolujte, zda hodnoty dávají smysl

---

## 🔍 Jak systém klasifikuje směsi

### Sumační metoda s M-faktory

Pro každou kategorii systém vypočítá:

```
Suma = Σ (koncentrace × M-faktor)
```

**Koncentrační limity (Generic Concentration Limits - GCL):**

| Kategorie | Limit GCL | M-faktor výchozí |
|-----------|-----------|------------------|
| Acute 1 | ≥ 0.1% | 1 |
| Chronic 1 | ≥ 0.1% | 1 |
| Chronic 2 | ≥ 1.0% | - |
| Chronic 3 | ≥ 1.0% | - |
| Chronic 4 | ≥ 1.0% | - |

### Klasifikační tabulka pro směsi

| Suma | Klasifikace směsi |
|------|-------------------|
| Suma Acute 1 ≥ 25% | Aquatic Acute 1 |
| Suma Chronic 1 ≥ 25% | Aquatic Chronic 1 |
| Suma Chronic 2 ≥ 25% | Aquatic Chronic 2 |
| 25% > Suma Chronic 1 ≥ 2.5% | Aquatic Chronic 3 |

---

## 🚀 Pokročilé funkce

### M-faktory

Pro velmi toxické látky můžete zadat **M-faktor** (multiplier):

```
M-faktor akutní:    [  10  ]   (např. pro LC50 < 0.1 mg/L)
M-faktor chronický: [ 100  ]   (např. pro NOEC < 0.01 mg/L)
```

**Výpočet:**
```
Efektivní koncentrace = koncentrace × M-faktor
```

### TODO: Budoucí funkce

> 🔄 **V přípravě:**
> - `is_rapidly_degradable` - pro přesnější Chronic klasifikaci
> - `is_bioaccumulative` - pro Chronic kategorie 4
> - Více NOEC hodnot pro různé organismy

---

## 📚 Reference

### Legislativa
- **Nařízení CLP:** (ES) č. 1272/2008, Příloha I, část 4.1
- **Guidance ECHA:** [Guidance on the Application of the CLP Criteria](https://echa.europa.eu/guidance-documents/guidance-on-clp)

### Testovací standardy
- **OECD 203:** Fish, Acute Toxicity Test (96h)
- **OECD 202:** Daphnia sp. Acute Immobilisation Test (48h)
- **OECD 201:** Freshwater Alga and Cyanobacteria, Growth Inhibition Test (72h)

### Online nástroje
- **ECHA Database:** https://echa.europa.eu/information-on-chemicals
- **PubChem:** https://pubchem.ncbi.nlm.nih.gov/

---

## ❓ Časté dotazy (FAQ)

### Q: Musím vyplnit všechny hodnoty?

**A:** Ne. Systém použije **nejnižší dostupnou hodnotu** pro klasifikaci. I jedna hodnota stačí.

### Q: Co když mám jen NOEC a ne LC50/EC50?

**A:** NOEC lze použít samostatně pro Chronic klasifikaci. Acute klasifikace vyžaduje LC50 nebo EC50.

### Q: Jak poznám, která hodnota je nejnižší?

**A:** Systém to udělá automaticky. V logu uvidíte, která hodnota byla použita.

### Q: Co dělat, když mám hodnotu v jiných jednotkách?

**A:** Převeďte hodnotu na mg/L (vodní testy) nebo mg/kg (savci). Např.:
- µg/L → mg/L: vydělte 1000
- g/L → mg/L: vynásobte 1000

### Q: Proč systém nezobrazuje Chronic kategorii, i když jsem zadal LC50?

**A:** Aktuálně systém předpokládá, že látky **nejsou rychle rozložitelné**. Pokud je vaše látka rychle rozložitelná, Chronic kategorie nemusí být přiřazena.

---

## 🛠️ Technická podpora

Pokud narazíte na problém nebo máte dotazy:
1. Zkontrolujte tento průvodce
2. Podívejte se do [walkthrough.md](walkthrough.md) pro technické detaily
3. Kontaktujte správce systému

---

**Verze dokumentu:** 1.0  
**Datum:** 2026-01-20  
**Autor:** CLP_Calculator Team
