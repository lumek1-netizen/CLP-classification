
import sys
import os

# Přidání aktuálního adresáře do sys.path pro importy
sys.path.append(os.getcwd())

from app.services.clp import apply_article_26_priorities

def test_article_26():
    print("--- Spouštím testy pro Článek 26 CLP ---")
    
    # 1. GHS06 potlačuje GHS07
    ghs = {'GHS06', 'GHS07'}
    h = {'H301', 'H302'} # H301 -> GHS06, H302 -> GHS07
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 1 (GHS06 + GHS07): {ghs} -> {res} | Očekáváno: {{'GHS06'}}")
    assert res == {'GHS06'}
    
    # 2. GHS05 potlačuje GHS07 (pokud je GHS07 jen pro H315/H319)
    ghs = {'GHS05', 'GHS07'}
    h = {'H314', 'H315'} # H314 -> GHS05, H315 -> GHS07
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 2a (GHS05 + H315): {ghs} -> {res} | Očekáváno: {{'GHS05'}}")
    assert res == {'GHS05'}
    
    ghs = {'GHS05', 'GHS07'}
    h = {'H314', 'H319'} # H314 -> GHS05, H319 -> GHS07
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 2b (GHS05 + H319): {ghs} -> {res} | Očekáváno: {{'GHS05'}}")
    assert res == {'GHS05'}
    
    # 3. GHS05 nepotlačuje GHS07, pokud je tam jiný důvod (např. H317 nebo H302)
    ghs = {'GHS05', 'GHS07'}
    h = {'H314', 'H315', 'H302'} 
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 3a (GHS05 + H315 + H302): {ghs} -> {res} | Očekáváno: {{'GHS05', 'GHS07'}}")
    assert res == {'GHS05', 'GHS07'}
    
    ghs = {'GHS05', 'GHS07'}
    h = {'H314', 'H317'} 
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 3b (GHS05 + H317): {ghs} -> {res} | Očekáváno: {{'GHS05', 'GHS07'}}")
    assert res == {'GHS05', 'GHS07'}
    
    # 4. GHS08 (H334) potlačuje GHS07 (H317, H315, H319)
    ghs = {'GHS08', 'GHS07'}
    h = {'H334', 'H317'} 
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 4a (GHS08/H334 + H317): {ghs} -> {res} | Očekáváno: {{'GHS08'}}")
    assert res == {'GHS08'}
    
    ghs = {'GHS08', 'GHS07'}
    h = {'H334', 'H315'} 
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 4b (GHS08/H334 + H315): {ghs} -> {res} | Očekáváno: {{'GHS08'}}")
    assert res == {'GHS08'}
    
    # 5. GHS08 nepotlačuje GHS07, pokud je tam jiný důvod (např. H335 nebo H302)
    ghs = {'GHS08', 'GHS07'}
    h = {'H334', 'H317', 'H335'} 
    res = apply_article_26_priorities(ghs, h)
    print(f"Test 5 (GHS08/H334 + H317 + H335): {ghs} -> {res} | Očekáváno: {{'GHS08', 'GHS07'}}")
    assert res == {'GHS08', 'GHS07'}
    
    print("\n--- Všechny testy pro Článek 26 PROŠLY ---")

if __name__ == "__main__":
    test_article_26()
