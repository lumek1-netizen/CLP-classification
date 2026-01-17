"""
Service layer pro správu látek.

Tento modul obsahuje business logiku pro vytváření, aktualizaci a validaci látek.
Odděluje business logiku od route handlers pro lepší testovatelnost a znovupoužitelnost.
"""

from typing import Optional
from flask import Request
from app.models import Substance
from app.services.clp import get_float_or_none, get_int_or_default


class SubstanceService:
    """Service pro správu chemických látek."""
    
    @staticmethod
    def create_substance_from_form(form_data: Request.form) -> Substance:
        """
        Vytvoří novou látku z formulářových dat.
        
        Args:
            form_data: Data z request.form
            
        Returns:
            Nová instance Substance (neuložená v DB)
            
        Raises:
            ValueError: Pokud jsou data nevalidní
        """
        # Základní informace
        name = form_data.get('name', '').strip()
        if not name:
            raise ValueError("Název látky je povinný")
        
        cas_number = form_data.get('cas_number', '').strip() or None
        ghs_codes = form_data.get('ghs_codes', '').strip() or None
        
        # H-věty
        health_list = form_data.getlist("health_h_phrases")
        env_list = form_data.getlist("env_h_phrases")
        health_h_phrases = ", ".join(health_list) if health_list else None
        env_h_phrases = ", ".join(env_list) if env_list else None
        
        # ATE hodnoty
        ate_oral = get_float_or_none(form_data, 'ate_oral')
        ate_dermal = get_float_or_none(form_data, 'ate_dermal')
        ate_inhalation_vapours = get_float_or_none(form_data, 'ate_inhalation_vapours')
        ate_inhalation_dusts_mists = get_float_or_none(form_data, 'ate_inhalation_dusts_mists')
        ate_inhalation_gases = get_float_or_none(form_data, 'ate_inhalation_gases')
        molecular_weight = get_float_or_none(form_data, 'molecular_weight')
        
        # M-faktory
        m_factor_acute = get_int_or_default(form_data, 'm_factor_acute', 1)
        m_factor_chronic = get_int_or_default(form_data, 'm_factor_chronic', 1)
        
        # SCL
        scl_limits = form_data.get('scl_limits', '').strip() or None
        
        # 2026 třídy nebezpečnosti
        is_lact = 'is_lact' in form_data
        ed_hh_cat = SubstanceService._parse_ed_category(form_data.get('ed_hh_cat', '0'))
        ed_env_cat = SubstanceService._parse_ed_category(form_data.get('ed_env_cat', '0'))
        is_pbt = 'is_pbt' in form_data
        is_vpvb = 'is_vpvb' in form_data
        is_pmt = 'is_pmt' in form_data
        is_vpvm = 'is_vpvm' in form_data
        has_ozone = 'has_ozone' in form_data
        is_svhc = 'is_svhc' in form_data
        is_reach_annex_xiv = 'is_reach_annex_xiv' in form_data
        is_reach_annex_xvii = 'is_reach_annex_xvii' in form_data
        
        # Vytvoření instance
        return Substance(
            name=name,
            cas_number=cas_number,
            ghs_codes=ghs_codes,
            health_h_phrases=health_h_phrases,
            env_h_phrases=env_h_phrases,
            ate_oral=ate_oral,
            ate_dermal=ate_dermal,
            ate_inhalation_vapours=ate_inhalation_vapours,
            ate_inhalation_dusts_mists=ate_inhalation_dusts_mists,
            ate_inhalation_gases=ate_inhalation_gases,
            molecular_weight=molecular_weight,
            m_factor_acute=m_factor_acute,
            m_factor_chronic=m_factor_chronic,
            scl_limits=scl_limits,
            is_lact=is_lact,
            ed_hh_cat=ed_hh_cat,
            ed_env_cat=ed_env_cat,
            is_pbt=is_pbt,
            is_vpvb=is_vpvb,
            is_pmt=is_pmt,
            is_vpvm=is_vpvm,
            has_ozone=has_ozone,
            is_svhc=is_svhc,
            is_reach_annex_xiv=is_reach_annex_xiv,
            is_reach_annex_xvii=is_reach_annex_xvii,
        )
    
    @staticmethod
    def update_substance_from_form(
        substance: Substance, 
        form_data: Request.form
    ) -> Substance:
        """
        Aktualizuje existující látku z formulářových dat.
        
        Args:
            substance: Instance látky k aktualizaci
            form_data: Data z request.form
            
        Returns:
            Aktualizovaná instance Substance
            
        Raises:
            ValueError: Pokud jsou data nevalidní
        """
        # Základní informace
        name = form_data.get('name', '').strip()
        if not name:
            raise ValueError("Název látky je povinný")
        
        substance.name = name
        substance.cas_number = form_data.get('cas_number', '').strip() or None
        substance.ghs_codes = form_data.get('ghs_codes', '').strip() or None
        
        # H-věty
        health_list = form_data.getlist("health_h_phrases")
        env_list = form_data.getlist("env_h_phrases")
        substance.health_h_phrases = ", ".join(health_list) if health_list else None
        substance.env_h_phrases = ", ".join(env_list) if env_list else None
        
        # ATE hodnoty
        substance.ate_oral = get_float_or_none(form_data, 'ate_oral')
        substance.ate_dermal = get_float_or_none(form_data, 'ate_dermal')
        substance.ate_inhalation_vapours = get_float_or_none(form_data, 'ate_inhalation_vapours')
        substance.ate_inhalation_dusts_mists = get_float_or_none(form_data, 'ate_inhalation_dusts_mists')
        substance.ate_inhalation_gases = get_float_or_none(form_data, 'ate_inhalation_gases')
        substance.molecular_weight = get_float_or_none(form_data, 'molecular_weight')
        
        # M-faktory
        substance.m_factor_acute = get_int_or_default(form_data, 'm_factor_acute', 1)
        substance.m_factor_chronic = get_int_or_default(form_data, 'm_factor_chronic', 1)
        
        # SCL
        substance.scl_limits = form_data.get('scl_limits', '').strip() or None
        
        # 2026 třídy
        substance.is_lact = 'is_lact' in form_data
        substance.ed_hh_cat = SubstanceService._parse_ed_category(form_data.get('ed_hh_cat', '0'))
        substance.ed_env_cat = SubstanceService._parse_ed_category(form_data.get('ed_env_cat', '0'))
        substance.is_pbt = 'is_pbt' in form_data
        substance.is_vpvb = 'is_vpvb' in form_data
        substance.is_pmt = 'is_pmt' in form_data
        substance.is_vpvm = 'is_vpvm' in form_data
        substance.has_ozone = 'has_ozone' in form_data
        substance.is_svhc = 'is_svhc' in form_data
        substance.is_reach_annex_xiv = 'is_reach_annex_xiv' in form_data
        substance.is_reach_annex_xvii = 'is_reach_annex_xvii' in form_data
        
        return substance
    
    @staticmethod
    def _parse_ed_category(value: str) -> Optional[int]:
        """
        Parsuje kategorii endokrinní disrupce.
        
        Args:
            value: Hodnota z formuláře ('0', '1', '2')
            
        Returns:
            None pro '0', jinak int kategorie
        """
        try:
            category = int(value)
            return category if category > 0 else None
        except (ValueError, TypeError):
            return None
