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
        
        # Ekotoxické parametry - standardní testy CLP
        lc50_fish_96h = get_float_or_none(form_data, 'lc50_fish_96h')
        ec50_daphnia_48h = get_float_or_none(form_data, 'ec50_daphnia_48h')
        ec50_algae_72h = get_float_or_none(form_data, 'ec50_algae_72h')
        noec_chronic = get_float_or_none(form_data, 'noec_chronic')
        ld50_oral_mammal = get_float_or_none(form_data, 'ld50_oral_mammal')
        ld50_dermal_mammal = get_float_or_none(form_data, 'ld50_dermal_mammal')
        lc50_inhalation_rat_4h = get_float_or_none(form_data, 'lc50_inhalation_rat_4h')
        
        # M-faktory
        m_factor_acute = get_int_or_default(form_data, 'm_factor_acute', 1)
        m_factor_chronic = get_int_or_default(form_data, 'm_factor_chronic', 1)
        
        # SCL
        scl_limits = form_data.get('scl_limits', '').strip() or None
        
        # 2026 třídy nebezpečnosti
        ed_hh_cat = SubstanceService._parse_ed_category(form_data.get('ed_hh_cat', '0'))
        ed_env_cat = SubstanceService._parse_ed_category(form_data.get('ed_env_cat', '0'))
        is_pbt = 'is_pbt' in form_data
        is_vpvb = 'is_vpvb' in form_data
        is_pmt = 'is_pmt' in form_data
        is_vpvm = 'is_vpvm' in form_data
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
            # Ekotoxické parametry
            lc50_fish_96h=lc50_fish_96h,
            ec50_daphnia_48h=ec50_daphnia_48h,
            ec50_algae_72h=ec50_algae_72h,
            noec_chronic=noec_chronic,
            ld50_oral_mammal=ld50_oral_mammal,
            ld50_dermal_mammal=ld50_dermal_mammal,
            lc50_inhalation_rat_4h=lc50_inhalation_rat_4h,
            # M-faktory a SCL
            m_factor_acute=m_factor_acute,
            m_factor_chronic=m_factor_chronic,
            scl_limits=scl_limits,
            # 2026 třídy
            ed_hh_cat=ed_hh_cat,
            ed_env_cat=ed_env_cat,
            is_pbt=is_pbt,
            is_vpvb=is_vpvb,
            is_pmt=is_pmt,
            is_vpvm=is_vpvm,
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
        
        # Ekotoxické parametry
        substance.lc50_fish_96h = get_float_or_none(form_data, 'lc50_fish_96h')
        substance.ec50_daphnia_48h = get_float_or_none(form_data, 'ec50_daphnia_48h')
        substance.ec50_algae_72h = get_float_or_none(form_data, 'ec50_algae_72h')
        substance.noec_chronic = get_float_or_none(form_data, 'noec_chronic')
        substance.ld50_oral_mammal = get_float_or_none(form_data, 'ld50_oral_mammal')
        substance.ld50_dermal_mammal = get_float_or_none(form_data, 'ld50_dermal_mammal')
        substance.lc50_inhalation_rat_4h = get_float_or_none(form_data, 'lc50_inhalation_rat_4h')
        
        # M-faktory
        substance.m_factor_acute = get_int_or_default(form_data, 'm_factor_acute', 1)
        substance.m_factor_chronic = get_int_or_default(form_data, 'm_factor_chronic', 1)
        
        # SCL
        substance.scl_limits = form_data.get('scl_limits', '').strip() or None
        
        # 2026 třídy
        substance.ed_hh_cat = SubstanceService._parse_ed_category(form_data.get('ed_hh_cat', '0'))
        substance.ed_env_cat = SubstanceService._parse_ed_category(form_data.get('ed_env_cat', '0'))
        substance.is_pbt = 'is_pbt' in form_data
        substance.is_vpvb = 'is_vpvb' in form_data
        substance.is_pmt = 'is_pmt' in form_data
        substance.is_vpvm = 'is_vpvm' in form_data
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
