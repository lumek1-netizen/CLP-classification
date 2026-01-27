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
    
    # Chybějící P-věty pro požár/skladování (Fyzikální nebezpečnost)
    "P370": "V případě požáru:",
    "P371": "V případě velkého požáru a velkého množství:",
    "P372": "Nebezpečí výbuchu při požáru.",
    "P373": "NEHASTE, pokud se oheň přiblíží k výbušninám.",
    "P375": "Kvůli nebezpečí výbuchu haste z dálky.",
    "P376": "Zastavte únik, můžete-li tak učinit bezpečně.",
    "P377": "Požár unikajícího plynu: Nehaste, nelze-li únik bezpečně zastavit.",
    "P378": "K uhašení použijte...",
    "P380": "Vykliďte prostor.",
    "P381": "V případě úniku odstraňte všechny zdroje zapálení.",
    "P240": "Uzemněte a upevněte obal a odběrové zařízení.",
    "P241": "Používejte elektrické/ventilační/osvětlovací/... zařízení do výbušného prostředí.",
    "P242": "Používejte nářadí z nejiskřícího kovu.",
    "P243": "Proveďte opatření proti výbojům statické elektřiny.",
    "P244": "Ventily a příslušenství udržujte bez oleje a maziv.",
    "P250": "Nevystavujte obrušování/nárazům/tření/...",
    "P222": "Nevystavujte styku se vzduchem.",
    "P223": "Zabraňte styku s vodou.",
    "P230": "Uchovávejte ve zvlhčeném stavu...",
    "P231": "Manipulace pod inertním plynem/...",
    "P232": "Chraňte před vlhkem.",
    "P235": "Uchovávejte v chladu.",
    "P401": "Skladujte v souladu s...",
    "P402": "Skladujte na suchém místě.",
    "P404": "Skladujte v uzavřeném obalu.",
    "P406": "Skladujte v obalu odolném proti korozi/…/obalu s odolnou vnitřní vrstvou.",
    "P407": "Mezi stohy/paletami ponechte vzduchovou mezeru.",
    "P410": "Chraňte před slunečním zářením.",
    "P411": "Skladujte při teplotě nepřesahující … °C/… °F.",
    "P412": "Nevystavujte teplotě přesahující 50 °C/122 °F.",
    "P413": "Skladujte volně ložené látky o hmotnosti větší než … kg/… liber při teplotě nepřesahující … °C/… °F.",
    "P420": "Skladujte odděleně od...",

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
    "P370+P372+P380+P373": "V případě požáru: Nebezpečí výbuchu. Vykliďte prostor. NEHASTE, pokud se oheň přiblíží k výbušninám.",
    "P370+P380+P375": "V případě požáru: Vykliďte prostor. Kvůli nebezpečí výbuchu haste z dálky.",
    "P371+P380+P375": "V případě velkého požáru a velkého množství: Vykliďte prostor. Kvůli nebezpečí výbuchu haste z dálky.",
    "P410+P403": "Chraňte před slunečním zářením. Skladujte na dobře větraném místě.",
    "P410+P412": "Chraňte před slunečním zářením. Nevystavujte teplotě přesahující 50 °C/122 °F.",
    "P403+P235": "Skladujte na dobře větraném místě. Uchovávejte v chladu.",
    "P231+P232": "Manipulace pod inertním plynem/... Chraňte před vlhkem.",
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

    # Fyzikální nebezpečnost
    "H200": ["P201", "P250", "P280", "P370+P372+P380+P373", "P401", "P501"],
    "H201": ["P201", "P250", "P280", "P370+P372+P380+P373", "P401", "P501"],
    "H202": ["P201", "P250", "P280", "P370+P372+P380+P373", "P401", "P501"],
    "H203": ["P201", "P250", "P280", "P370+P372+P380+P373", "P401", "P501"],
    "H204": ["P210", "P240", "P250", "P280", "P370+P372+P380+P373", "P401", "P501"],
    "H205": ["P210", "P230", "P240", "P250", "P280", "P370+P372+P380+P373", "P401", "P501"],
    "H220": ["P210", "P377", "P381", "P403"],
    "H221": ["P210", "P377", "P381", "P403"],
    "H222": ["P210", "P211", "P251", "P410+P412"],
    "H223": ["P210", "P211", "P251", "P410+P412"],
    "H229": ["P210", "P251", "P410+P412"],
    "H224": ["P210", "P233", "P240", "P241", "P242", "P243", "P280", "P303+P361+P353", "P370+P378", "P403+P235", "P501"],
    "H225": ["P210", "P233", "P240", "P241", "P242", "P243", "P280", "P303+P361+P353", "P370+P378", "P403+P235", "P501"],
    "H226": ["P210", "P233", "P240", "P241", "P242", "P243", "P280", "P303+P361+P353", "P370+P378", "P403+P235", "P501"],
    "H228": ["P210", "P240", "P241", "P280", "P370+P378"],
    "H240": ["P210", "P234", "P235", "P240", "P280", "P370+P372+P380+P373", "P403", "P411", "P420", "P501"],
    "H241": ["P210", "P234", "P235", "P240", "P280", "P370+P380+P375", "P403", "P411", "P420", "P501"],
    "H242": ["P210", "P234", "P235", "P240", "P280", "P370+P378", "P403", "P411", "P420", "P501"],
    "H250": ["P210", "P222", "P231", "P233", "P280", "P302+P335+P334", "P370+P378"],
    "H251": ["P235", "P280", "P407", "P413", "P420"],
    "H252": ["P235", "P280", "P407", "P413", "P420"],
    "H260": ["P223", "P231+P232", "P280", "P302+P335+P334", "P370+P378", "P402+P404", "P501"],
    "H261": ["P223", "P231+P232", "P280", "P302+P335+P334", "P370+P378", "P402+P404", "P501"],
    "H270": ["P220", "P244", "P370+P376"],
    "H271": ["P210", "P220", "P280", "P283", "P306+P360", "P371+P380+P375", "P370+P378", "P501"],
    "H272": ["P210", "P220", "P280", "P370+P378", "P501"],
    "H280": ["P410+P403"],
    "H281": ["P282", "P336+P315", "P403"],
    "H290": ["P234", "P390", "P406"],

    # Repro variants (detailed)
    "H360F": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H360D": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H360FD": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H360Fd": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H360Df": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H361f": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H361d": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
    "H361fd": ["P201", "P202", "P280", "P308+P313", "P405", "P501"],
}
