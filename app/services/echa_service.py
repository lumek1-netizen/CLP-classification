import requests
import logging
import re

logger = logging.getLogger(__name__)

class ECHAService:
    """
    Služba pro komunikaci s ECHA CHEM API (verze 2026).
    """
    BASE_URL = "https://chem.echa.europa.eu"

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://chem.echa.europa.eu",
            "Referer": "https://chem.echa.europa.eu/substance-search"
        })

    def fetch_data(self, cas_or_ec):
        """
        Získá kompletní data o látce z ECHA API.
        
        Metoda stahuje:
        1. Základní info a ID látky.
        2. Harmonizovanou klasifikaci (C&L).
        3. Legislativní povinnosti (SVHC, PBT, atd.).
        
        Args:
            cas_or_ec: CAS nebo EC číslo látky.
            
        Returns:
            Dict s daty látky nebo dict s klíčem 'error'.
        """
        try:
            substance_id = self._get_substance_id(cas_or_ec)
            if not substance_id:
                return {"error": "Látka nebyla v databázi ECHA nalezena."}

            detail = self._get_detail(substance_id)
            harmonised = self._get_harmonised_info(substance_id)
            obligations = self._get_obligations_summary(substance_id)

            return self._parse_response(detail, harmonised, obligations)

        except requests.exceptions.RequestException as e:
            logger.error(f"Chyba při komunikaci s ECHA API: {e}")
            return {"error": f"Nepodařilo se spojit s ECHA API: {str(e)}"}
        except Exception as e:
            logger.exception("Neočekávaná chyba při zpracování dat z ECHA")
            return {"error": f"Interní chyba při zpracování dat: {str(e)}"}

    def _get_substance_id(self, query):
        url = f"{self.BASE_URL}/api-substance/v1/substance"
        params = {
            "pageIndex": 1,
            "pageSize": 10,
            "searchText": query
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        
        hits = data.get("items") or data.get("content") or []
        if not hits:
            return None

        # 1. Pokus o přesnou shodu
        for hit in hits:
            sub = hit.get("substanceIndex") or hit
            
            # Získání CAS (může být string nebo list)
            cas_data = sub.get("rmlCas") or sub.get("casNumber")
            ec_data = sub.get("rmlEc") or sub.get("ecNumber")
            
            if self._matches_query(query, cas_data) or self._matches_query(query, ec_data):
                return sub.get("rmlId") or sub.get("id")

        # 2. Fallback na první výsledek
        first_sub = hits[0].get("substanceIndex") or hits[0]
        return first_sub.get("rmlId") or first_sub.get("id")

    def _matches_query(self, query, data):
        if not data:
            return False
        if isinstance(data, list):
            return query in data
        return query == data

    def _get_detail(self, substance_id):
        url = f"{self.BASE_URL}/api-substance/v1/substance/{substance_id}"
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _get_harmonised_info(self, substance_id):
        # 1. Získáme seznam klasifikací
        url_classes = f"{self.BASE_URL}/api-cnl-inventory/harmonized/{substance_id}/classifications"
        try:
            r = self.session.get(url_classes, timeout=self.timeout)
            r.raise_for_status()
            classes = r.json()
            items = classes.get("items", [])
            if not items:
                return None
            
            # Vybereme prominentní klasifikaci (isProminentFlag), pokud existuje,
            # jinak vezmeme první v seznamu.
            target_item = next((i for i in items if i.get("isProminentFlag")), items[0])
            class_id = target_item.get("classificationId")
            if not class_id:
                return None
            
            # 2. Získáme konkrétní doplňující data pro tuto klasifikaci
            res = {"class_id": class_id}
            
            endpoints = {
                "scls": "specific-concentration-limits",
                "pictograms": "pictograms",
                "labelling": "labelling",
                "ates": "acute-toxicity-estimates"
            }
            
            for key, path in endpoints.items():
                url = f"{self.BASE_URL}/api-cnl-inventory/harmonized/{path}/{class_id}"
                try:
                    r_detail = self.session.get(url, timeout=self.timeout)
                    r_detail.raise_for_status()
                    res[key] = r_detail.json()
                except Exception as e:
                    logger.warning(f"Nepodařilo se získat {key} pro {class_id}: {e}")
                    res[key] = None
                    
            return res
        except requests.exceptions.RequestException as e:
            logger.warning(f"Nepodařilo se získat harmonizovanou klasifikaci pro {substance_id}: {e}")
            return None

    def _get_obligations_summary(self, substance_id):
        # Spolehlivější endpoint používaný přímo webovým rozhraním ECHA
        url = f"{self.BASE_URL}/api-obligation-substance/v1/{substance_id}/summary/"
        params = {"rmlId": substance_id}
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def _parse_response(self, detail, harmonised, obligations_summary):
        # Pomocná funkce pro získání stringu z možného seznamu nebo fallbacku
        def _get_val(d, keys):
            for k in keys:
                val = d.get(k)
                if val:
                    if isinstance(val, list):
                        return val[0]
                    return val
            return None

        res = {
            "name": _get_val(detail, ["rmlName", "substanceName"]),
            "cas": _get_val(detail, ["rmlCas", "casNumber"]),
            "ec": _get_val(detail, ["rmlEc", "ecNumber"]),
            "is_svhc": False,
            "is_reach_annex_xiv": False,
            "is_reach_annex_xvii": False,
            "is_pbt": False,
            "is_vpvb": False,
            "is_pmt": False,
            "is_vpvm": False,
            "scl_limits": [],
            "ghs_symbols": [],
            "h_phrases": [],
            "ate_values": {}
        }

        # Zpracování legislativních seznamů z nového endpointu
        if obligations_summary and "items" in obligations_summary:
            for item in obligations_summary["items"]:
                label = item.get("legalObligationLabel", "").upper()
                type_id = item.get("legalObligationType", "").lower()
                
                # SVHC detekce - musí to být skutečný Candidate List
                if ("SVHC" in label or "CANDIDATE LIST" in label) and "WITHDRAWN" not in label:
                    res["is_svhc"] = True
                
                if "ANNEX XIV" in label or type_id == "annexxiv":
                    res["is_reach_annex_xiv"] = True
                
                if "RESTRICTION LIST" in label or "ANNEX XVII" in label or type_id == "restrictionlist":
                    res["is_reach_annex_xvii"] = True
                
                if "PBT" in label: res["is_pbt"] = True
                if "VPVB" in label: res["is_vpvb"] = True
                if "PMT" in label: res["is_pmt"] = True
                if "VPVM" in label: res["is_vpvm"] = True

        if not harmonised:
            return res

        # Zpracování SCL (Specifické koncentrační limity)
        scls = harmonised.get("scls")
        if scls and "items" in scls:
            for item in scls["items"]:
                cond_range = item.get("concentrationRange")
                hazards = item.get("hazards", [])
                if cond_range and hazards:
                    parsed_val = self._parse_scl_value(cond_range)
                    if parsed_val:
                        for haz in hazards:
                            hazard_code = haz.get("hazardClassAndCategoryCode")
                            if hazard_code:
                                res["scl_limits"].append(f"{hazard_code}: {parsed_val}")

        # Zpracování piktogramů
        pictograms = harmonised.get("pictograms")
        if pictograms and "items" in pictograms:
            for item in pictograms["items"]:
                code = item.get("code")
                if code:
                    res["ghs_symbols"].append(code)

        # Zpracování H-vět
        labelling = harmonised.get("labelling")
        if labelling and "items" in labelling:
            for item in labelling["items"]:
                h_code = item.get("hazardStatement", {}).get("hazardStatementCode")
                if h_code:
                    res["h_phrases"].append(h_code)

        # Zpracování ATE hodnot
        ates = harmonised.get("ates")
        if ates and "items" in ates:
            for item in ates["items"]:
                val = item.get("acuteToxicity", {}).get("estimation")
                unit = item.get("acuteToxicity", {}).get("unit")
                route = item.get("routeExposure", {}).get("routeOfExposure", "").lower()
                
                if val is not None and route:
                    key = route
                    if "inhalation" in route:
                        # Rozlišení typu inhalace podle jednotek
                        if unit == "ppmV":
                            key = "inhalation_gas"
                        elif unit == "mg/L":
                            # ECHA API často nerozlišuje páru od prachu přímo v routeOfExposure
                            # Pro teď dáme páru jako default pro mg/L, ale v JS můžeme dát volbu
                            key = "inhalation_vapour"
                    
                    res["ate_values"][key] = val

        return res

    def _parse_scl_value(self, value_str):
        """
        Převádí "C ≥ 15 %" na ">= 15" nebo "5 % ≤ C < 15 %" na ">= 5; < 15"
        """
        # Odstraníme procenta a mezery
        s = value_str.replace("%", "").strip()
        
        # Jednoduchý limit: C ≥ 15
        simple_match = re.search(r"C\s*([≥>=<≤]+)\s*([\d\.,]+)", s)
        # Rozmezí: 5 ≤ C < 15
        range_match = re.search(r"([\d\.,]+)\s*([≤<]+)\s*C\s*([<≤])\s*([\d\.,]+)", s)

        if range_match:
            # Převracíme první část: 5 ≤ C  => C ≥ 5
            val1 = range_match.group(1).replace(",", ".")
            op1 = ">=" if "≤" in range_match.group(2) else ">"
            op2 = range_match.group(3).replace("≤", "<=").replace("<", "<")
            val2 = range_match.group(4).replace(",", ".")
            return f"{op1} {val1}; {op2} {val2}"
        
        if simple_match:
            op = simple_match.group(1).replace("≥", ">=").replace("≤", "<=")
            val = simple_match.group(2).replace(",", ".")
            return f"{op} {val}"

        return None
