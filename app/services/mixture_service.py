"""
Service layer pro správu směsí.

Obsahuje business logiku pro vytváření, aktualizaci a validaci směsí.
"""

from typing import List, Dict, Any


class MixtureService:
    """Service pro správu chemických směsí."""
    
    @staticmethod
    def parse_and_validate_components(
        form_data
    ) -> List[Dict[str, Any]]:
        """
        Parsuje a validuje komponenty směsi z formuláře.
        
        Provádí následující validace:
        - Koncentrace musí být kladná
        - Žádné duplicitní látky
        - Celková koncentrace nesmí přesáhnout 100%
        - Směs musí mít alespoň jednu komponentu
        
        Args:
            form_data: Data z request.form
            
        Returns:
            Seznam validovaných komponent ve formátu:
            [{"substance_id": int, "concentration": float}, ...]
            
        Raises:
            ValueError: Pokud jsou data nevalidní
            
        Examples:
            >>> components = MixtureService.parse_and_validate_components(request.form)
            >>> components
            [{"substance_id": 1, "concentration": 50.0}, 
             {"substance_id": 2, "concentration": 30.0}]
        """
        concentrations = form_data.getlist("concentration")
        substance_ids = form_data.getlist("substance_id")
        
        components = []
        total_concentration = 0.0
        seen_substance_ids = set()
        
        for conc_str, sub_id_str in zip(concentrations, substance_ids):
            # Přeskočit prázdné řádky
            if not conc_str or not sub_id_str:
                continue
            
            try:
                concentration = float(conc_str)
                substance_id = int(sub_id_str)
            except ValueError:
                raise ValueError(
                    f"Neplatná hodnota: koncentrace='{conc_str}', látka='{sub_id_str}'"
                )
            
            # Validace koncentrace
            if concentration <= 0:
                raise ValueError(
                    f"Koncentrace musí být kladná (zadáno: {concentration}%)"
                )
            
            # Kontrola duplicit
            if substance_id in seen_substance_ids:
                raise ValueError(
                    f"Látka s ID {substance_id} je ve směsi duplicitně"
                )
            
            # Kontrola celkové koncentrace
            total_concentration += concentration
            if total_concentration > 100.001:  # Tolerance pro zaokrouhlovací chyby
                raise ValueError(
                    f"Celková koncentrace přesahuje 100% (aktuálně: {total_concentration:.2f}%)"
                )
            
            components.append({
                "substance_id": substance_id,
                "concentration": concentration
            })
            seen_substance_ids.add(substance_id)
        
        # Kontrola minimálního počtu komponent
        if not components:
            raise ValueError("Směs musí obsahovat alespoň jednu složku")
        
        return components
