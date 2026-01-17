"""
Konstanty a mapování pro P-věty (Pokyny pro bezpečné zacházení) podle nařízení CLP.
"""

# Texty P-vět v češtině
P_PHRASES_TEXT = {
    # Všeobecné
    "P101": "Je-li nutná lékařská pomoc, mějte po ruce obal nebo štítek výrobku.",
    "P102": "Uchovávejte mimo dosah dětí.",
    "P103": "Pečlivě si přečtěte všechny pokyny a řiďte se jimi.",

    # Prevence
    "P201": "Před použitím si obstarejte speciální instrukce.",
    "P202": "Nepoužívejte, dokud jste si nepřečetli všechny bezpečnostní pokyny a neporozuměli jim.",
    "P210": "Chraňte před teplem, horkými povrchy, jiskrami, otevřeným ohněm a jinými zdroji zapálení. Zákaz kouření.",
    "P220": "Uchovávejte odděleně od oděvů a jiných hořlavých materiálů.",
    "P233": "Uchovávejte obal těsně uzavřený.",
    "P234": "Uchovávejte pouze v původním balení.",
    "P260": "Nevdechujte prach/dým/plyn/mlhu/páry/aerosoly.",
    "P261": "Zamezte vdechování prachu/dýmu/plynu/mlhy/par/aerosolů.",
    "P262": "Zabraňte styku s očima, kůží nebo oděvem.",
    "P263": "Zabraňte styku během těhotenství a kojení.",
    "P264": "Po manipulaci důkladně omyjte ruce a zasažené části těla.",
    "P270": "Při používání tohoto výrobku nejezte, nepijte ani nekuřte.",
    "P271": "Používejte pouze venku nebo v dobře větraných prostorách.",
    "P272": "Kontaminovaný pracovní oděv neodnášejte z pracoviště.",
    "P273": "Zabraňte uvolnění do životního prostředí.",
    "P280": "Používejte ochranné rukavice/ochranný oděv/ochranné brýle/obličejový štít.",
    "P284": "V případě nedostatečného větrání používejte vybavení pro ochranu dýchacích cest.",
    
    # Reakce
    "P301": "PŘI POŽITÍ:",
    "P302": "PŘI STYKU S KŮŽÍ:",
    "P303": "PŘI STYKU S KŮŽÍ (nebo s vlasy):",
    "P304": "PŘI VDECHNUTÍ:",
    "P305": "PŘI ZASAŽENÍ OČÍ:",
    "P308": "PŘI expozici nebo podezření na ni:",
    "P310": "Okamžitě volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P311": "Volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P312": "Necítíte-li se dobře, volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P313": "Vyhledejte lékařskou pomoc/ošetření.",
    "P314": "Necítíte-li se dobře, vyhledejte lékařskou pomoc/ošetření.",
    "P320": "Je nutné odborné ošetření (viz na tomto štítku).",
    "P321": "Odborné ošetření (viz na tomto štítku).",
    "P330": "Vypláchněte ústa.",
    "P331": "NEVYVOLÁVEJTE zvracení.",
    "P332": "Při podráždění kůže:",
    "P333": "Při podráždění kůže nebo vyrážce:",
    "P337": "Přetrvává-li podráždění očí:",
    "P340": "Přeneste osobu na čerstvý vzduch a ponechte ji v poloze usnadňující dýchání.",
    "P362": "Kontaminovaný oděv svlékněte.",
    "P363": "Kontaminovaný oděv před opětovným použitím vyperte.",
    "P391": "Uniklý produkt seberte.",

    # Skladování
    "P403": "Skladujte na dobře větraném místě.",
    "P405": "Skladujte uzamčené.",
    
    # Odstraňování
    "P501": "Odstraňte obsah/obal v souladu s místními předpisy.",
    "P502": "Informujte se u výrobce nebo dodavatele o regeneraci nebo recyklaci.",
}

# Kombinované P-věty (pro zjednodušení logiky je definujeme jako samostatné klíče, pokud se používají)
# V praxi se často skládají, např. P301+P310. Zde mapujeme kód na text.
P_COMBINATIONS = {
    "P301+P310": "PŘI POŽITÍ: Okamžitě volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P301+P312": "PŘI POŽITÍ: Necítíte-li se dobře, volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P301+P330+P331": "PŘI POŽITÍ: Vypláchněte ústa. NEVYVOLÁVEJTE zvracení.",
    "P302+P352": "PŘI STYKU S KŮŽÍ: Omyjte velkým množstvím vody.",
    "P303+P361+P353": "PŘI STYKU S KŮŽÍ (nebo s vlasy): Veškeré kontaminované části oděvu okamžitě svlékněte. Opláchněte kůži vodou [nebo osprchujte].",
    "P304+P340": "PŘI VDECHNUTÍ: Přeneste osobu na čerstvý vzduch a ponechte ji v poloze usnadňující dýchání.",
    "P305+P351+P338": "PŘI ZASAŽENÍ OČÍ: Několik minut opatrně vyplachujte vodou. Vyjměte kontaktní čočky, jsou-li nasazeny a pokud je lze vyjmout snadno. Pokračujte ve vyplachování.",
    "P308+P313": "PŘI expozici nebo podezření na ni: Vyhledejte lékařskou pomoc/ošetření.",
    "P333+P313": "Při podráždění kůže nebo vyrážce: Vyhledejte lékařskou pomoc/ošetření.",
    "P337+P313": "Přetrvává-li podráždění očí: Vyhledejte lékařskou pomoc/ošetření.",
    "P342+P311": "Při dýchacích potížích: Volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P361+P364": "Veškeré kontaminované části oděvu okamžitě svlékněte. Kontaminovaný oděv před opětovným použitím vyperte.",
    "P362+P364": "Kontaminovaný oděv svlékněte a před opětovným použitím ho vyperte.",
    "P332+P313": "Při podráždění kůže: Vyhledejte lékařskou pomoc/ošetření.",
    "P308+P311": "PŘI expozici nebo podezření na ni: Volejte TOXIKOLOGICKÉ INFORMAČNÍ STŘEDISKO/lékaře.",
    "P370+P378": "V případě požáru: K uhašení použijte...",
    "P403+P233": "Skladujte na dobře větraném místě. Uchovávejte obal těsně uzavřený.",
}

# Sloučení pro snazší lookup
ALL_P_PHRASES = {**P_PHRASES_TEXT, **P_COMBINATIONS}

# Mapování H-vět na doporučené P-věty
# Toto je zjednodušené mapování vycházející z typických požadavků CLP (Annex IV).
# Pro plnou logiku by bylo nutné zohlednit fyzikální stav, zda jde o spotřebitelské balení atd.
H_TO_P_MAP = {
    # Akutní toxicita - orální
    "H300": ["P264", "P270", "P301+P310", "P321", "P330", "P405", "P501"], # Acute Tox 1/2
    "H301": ["P264", "P270", "P301+P310", "P321", "P330", "P405", "P501"], # Acute Tox 3
    "H302": ["P264", "P270", "P301+P312", "P330", "P501"],                 # Acute Tox 4

    # Akutní toxicita - dermální
    "H310": ["P262", "P264", "P270", "P280", "P302+P352", "P310", "P321", "P361+P364", "P405", "P501"],
    "H311": ["P280", "P302+P352", "P312", "P321", "P361+P364", "P405", "P501"],
    "H312": ["P280", "P302+P352", "P312", "P321", "P362+P364", "P501"],

    # Akutní toxicita - inhalační
    "H330": ["P260", "P271", "P284", "P304+P340", "P310", "P320", "P403+P233", "P405", "P501"],
    "H331": ["P261", "P271", "P304+P340", "P311", "P321", "P403+P233", "P405", "P501"],
    "H332": ["P261", "P271", "P304+P340", "P312"],

    # Žíravost/Dráždivost pro kůži
    "H314": ["P260", "P264", "P280", "P301+P330+P331", "P303+P361+P353", "P363", "P304+P340", "P310", "P321", "P305+P351+P338", "P405", "P501"],
    "H315": ["P264", "P280", "P302+P352", "P321", "P332+P313", "P362+P364"],

    # Poškození/Podráždění očí
    "H318": ["P280", "P305+P351+P338", "P310"],
    "H319": ["P264", "P280", "P305+P351+P338", "P337+P313"],

    # Senzibilizace
    "H317": ["P261", "P272", "P280", "P302+P352", "P333+P313", "P362+P364", "P501"],
    "H334": ["P261", "P284", "P304+P340", "P342+P311", "P501"],

    # CMR (Mutagenita, Karcinogenita, Reprodukční toxicita)
    "H340": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H341": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H350": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H351": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H360": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H361": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H362": ["P201", "P260", "P263", "P264", "P270", "P308+P313"],

    # STOT (Specifická toxicita pro cílové orgány)
    "H370": ["P260", "P264", "P270", "P308+P311", "P321", "P405", "P501"],
    "H371": ["P260", "P264", "P270", "P308+P311", "P405", "P501"],
    "H335": ["P261", "P271", "P304+P340", "P312", "P403+P233", "P405", "P501"],
    "H336": ["P261", "P271", "P304+P340", "P312", "P403+P233", "P405", "P501"],
    "H372": ["P260", "P264", "P270", "P314", "P501"],
    "H373": ["P260", "P314", "P501"],

    # Aspirační toxicita
    "H304": ["P301+P310", "P331", "P405", "P501"],

    # Nebezpečnost pro vodní prostředí
    "H400": ["P273", "P391", "P501"],
    "H410": ["P273", "P391", "P501"],
    "H411": ["P273", "P391", "P501"],
    "H412": ["P273", "P501"],
    "H413": ["P273", "P501"],
    
    # Ozón
    "H420": ["P502"],
}
