"""
Service layer pro správu směsí.

Obsahuje business logiku pro vytváření, aktualizaci a validaci směsí.
"""

from typing import List, Dict, Any, Set
from app.extensions import db
from app.models import ComponentType


class MixtureService:
    """Service pro správu chemických směsí."""
    
    @staticmethod
    def parse_and_validate_components(
        form_data,
        mixture_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Parsuje a validuje komponenty směsi z formuláře.
        
        Provádí následující validace:
        - Koncentrace musí být kladná
        - Žádné duplicitní látky/směsi
        - Celková koncentrace nesmí přesáhnout 100%
        - Směs musí mít alespoň jednu komponentu
        - Kontrola cyklických závislostí při použití směsí
        
        Args:
            form_data: Data z request.form
            mixture_id: ID upravované směsi (pro validaci cyklických závislostí)
            
        Returns:
            Seznam validovaných komponent
            
        Raises:
            ValueError: Pokud jsou data nevalidní
        """
        concentrations = form_data.getlist("concentration")
        component_types = form_data.getlist("component_type")
        substance_ids = form_data.getlist("substance_id")
        mixture_ids = form_data.getlist("mixture_id")
        
        components = []
        total_concentration = 0.0
        seen_substance_ids = set()
        seen_mixture_ids = set()
        
        # Zajistit, že všechny seznamy mají stejnou délku
        max_len = max(len(concentrations), len(component_types), len(substance_ids), len(mixture_ids))
        while len(component_types) < max_len:
            component_types.append("substance")
        while len(substance_ids) < max_len:
            substance_ids.append("")
        while len(mixture_ids) < max_len:
            mixture_ids.append("")
        
        for i, conc_str in enumerate(concentrations):
            # Přeskočit prázdné řádky
            if not conc_str:
                continue
            
            comp_type = component_types[i] if i < len(component_types) else "substance"
            sub_id_str = substance_ids[i] if i < len(substance_ids) else ""
            mix_id_str = mixture_ids[i] if i < len(mixture_ids) else ""
            
            try:
                concentration = float(conc_str)
            except ValueError:
                raise ValueError(f"Neplatná hodnota koncentrace: '{conc_str}'")
            
            # Validace koncentrace
            if concentration <= 0:
                raise ValueError(f"Koncentrace musí být kladná (zadáno: {concentration}%)")
            
            # Kontrola celkové koncentrace
            total_concentration += concentration
            if total_concentration > 100.001:
                raise ValueError(
                    f"Celková koncentrace přesahuje 100% (aktuálně: {total_concentration:.2f}%)"
                )
            
            # Zpracování podle typu komponenty
            if comp_type == "substance":
                if not sub_id_str:
                    raise ValueError("Není vybrána látka")
                try:
                    substance_id = int(sub_id_str)
                except ValueError:
                    raise ValueError(f"Neplatné ID látky: '{sub_id_str}'")
                
                if substance_id in seen_substance_ids:
                    raise ValueError(f"Látka s ID {substance_id} je ve směsi duplicitně")
                
                components.append({
                    "component_type": ComponentType.SUBSTANCE,
                    "substance_id": substance_id,
                    "concentration": concentration
                })
                seen_substance_ids.add(substance_id)
                
            elif comp_type == "mixture":
                if not mix_id_str:
                    raise ValueError("Není vybrána směs")
                try:
                    component_mixture_id = int(mix_id_str)
                except ValueError:
                    raise ValueError(f"Neplatné ID směsi: '{mix_id_str}'")
                
                if component_mixture_id in seen_mixture_ids:
                    raise ValueError(f"Směs s ID {component_mixture_id} je ve směsi duplicitně")
                
                # Validace cyklických závislostí
                if mixture_id is not None:
                    MixtureService.validate_no_circular_dependency(mixture_id, component_mixture_id)
                
                components.append({
                    "component_type": ComponentType.MIXTURE,
                    "component_mixture_id": component_mixture_id,
                    "concentration": concentration
                })
                seen_mixture_ids.add(component_mixture_id)
        
        # Kontrola minimálního počtu komponent
        if not components:
            raise ValueError("Směs musí obsahovat alespoň jednu složku")
        
        return components
    
    @staticmethod
    def validate_no_circular_dependency(
        mixture_id: int, 
        component_mixture_id: int, 
        visited: Set[int] = None
    ) -> None:
        """
        Validuje, že přidání směsi jako komponenty nevytvoří cyklickou závislost.
        
        Args:
            mixture_id: ID směsi, do které přidáváme komponentu
            component_mixture_id: ID směsi, kterou chceme přidat jako komponentu
            visited: Množina již navštívených směsí (pro rekurzi)
            
        Raises:
            ValueError: Pokud by vznikla cyklická závislost
        """
        from app.models import MixtureComponent
        
        if visited is None:
            visited = set()
        
        # Pokud se snažíme přidat směs samu do sebe
        if mixture_id == component_mixture_id:
            raise ValueError("Směs nemůže obsahovat samu sebe")
        
        # Pokud jsme tuto směs již navštívili, máme cyklus
        if component_mixture_id in visited:
            raise ValueError("Detekována cyklická závislost mezi směsmi")
        
        visited.add(component_mixture_id)
        
        # Získat všechny komponenty typu mixture z component_mixture_id
        sub_components = MixtureComponent.query.filter_by(
            mixture_id=component_mixture_id,
            component_type=ComponentType.MIXTURE
        ).all()
        
        # Rekurzivně zkontrolovat každou pod-směs
        for comp in sub_components:
            if comp.component_mixture_id == mixture_id:
                raise ValueError(
                    f"Cyklická závislost: směs {component_mixture_id} již obsahuje směs {mixture_id}"
                )
            MixtureService.validate_no_circular_dependency(
                mixture_id, 
                comp.component_mixture_id, 
                visited.copy()
            )
    
    @staticmethod
    def expand_mixture_components(mixture_id: int) -> List[Dict[str, Any]]:
        """
        Rozbalí všechny komponenty směsi (včetně vnořených směsí) na jednotlivé látky.
        
        Přepočítá koncentrace látek podle jejich výskytu ve vnořených směsích.
        Například: Směs A obsahuje 50% směsi B, směs B obsahuje 20% látky X
        → výsledná koncentrace látky X ve směsi A je 10%
        
        Args:
            mixture_id: ID směsi k rozbalení
            
        Returns:
            Seznam slovníků s substance_id a concentration pro každou látku
            
        Example:
            >>> MixtureService.expand_mixture_components(1)
            [{'substance_id': 5, 'concentration': 10.0}, 
             {'substance_id': 7, 'concentration': 15.5}]
        """
        from app.models import MixtureComponent, Substance
        
        # Slovník pro agregaci koncentrací látek
        substance_concentrations: Dict[int, float] = {}
        
        def expand_recursive(mix_id: int, parent_concentration: float = 100.0):
            """Rekurzivní funkce pro rozbalení směsi."""
            components = MixtureComponent.query.filter_by(mixture_id=mix_id).all()
            
            for comp in components:
                # Vypočítat efektivní koncentraci vzhledem k rodičovské směsi
                effective_concentration = (comp.concentration * parent_concentration) / 100.0
                
                if comp.component_type == ComponentType.SUBSTANCE:
                    # Je to látka - přidat/akumulovat koncentraci
                    if comp.substance_id in substance_concentrations:
                        substance_concentrations[comp.substance_id] += effective_concentration
                    else:
                        substance_concentrations[comp.substance_id] = effective_concentration
                        
                elif comp.component_type == ComponentType.MIXTURE:
                    # Je to směs - rekurzivně rozbalit
                    expand_recursive(comp.component_mixture_id, effective_concentration)
        
        # Spustit rekurzivní rozbalení
        expand_recursive(mixture_id)
        
        # Převést na seznam
        result = [
            {"substance_id": sub_id, "concentration": conc}
            for sub_id, conc in substance_concentrations.items()
        ]
        
        return result

