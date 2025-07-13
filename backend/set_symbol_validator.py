#!/usr/bin/env python3
"""
Set Symbol Validator - Correlates AI-identified set symbols with known set information
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class SetSymbolValidator:
    """Validates set symbols against known Magic: The Gathering sets"""
    
    def __init__(self):
        """Initialize with known set symbol descriptions"""
        # Common set symbol descriptions mapped to set codes/names
        self.symbol_patterns = {
            # Commander sets
            "commander 2017": {
                "codes": ["c17", "cma"],
                "names": ["commander 2017", "commander anthology"],
                "symbols": ["shield with sword", "dragon head", "stylized dragon", "dragon symbol"]
            },
            "commander 2018": {
                "codes": ["c18"],
                "names": ["commander 2018"],
                "symbols": ["shield", "stylized shield", "shield symbol"]
            },
            "commander 2015": {
                "codes": ["c15"],
                "names": ["commander 2015"],
                "symbols": ["stylized c", "commander symbol"]
            },
            "commander 2011": {
                "codes": ["cmd"],
                "names": ["commander 2011"],
                "symbols": ["triangle", "stylized triangle"]
            },
            
            # Core sets
            "magic 2012": {
                "codes": ["m12"],
                "names": ["magic 2012"],
                "symbols": ["m12", "stylized m"]
            },
            "unlimited edition": {
                "codes": ["2ed"],
                "names": ["unlimited edition", "unlimited"],
                "symbols": ["no symbol", "none visible", "early set"]
            },
            
            # Expansion sets
            "modern horizons 2": {
                "codes": ["mh2"],
                "names": ["modern horizons 2"],
                "symbols": ["horizons symbol", "modern horizons", "mh2"]
            },
            "eternal masters": {
                "codes": ["ema"],
                "names": ["eternal masters"],
                "symbols": ["eternal symbol", "masters symbol"]
            },
            "urza's legacy": {
                "codes": ["ulg"],
                "names": ["urza's legacy"],
                "symbols": ["urza symbol", "legacy symbol", "gear"]
            },
            "rise of the eldrazi": {
                "codes": ["roe"],
                "names": ["rise of the eldrazi"],
                "symbols": ["eldrazi symbol", "hedron", "geometric"]
            },
            "ultimate masters": {
                "codes": ["uma"],
                "names": ["ultimate masters"],
                "symbols": ["masters symbol", "ultimate symbol"]
            },
            "time spiral": {
                "codes": ["tsp"],
                "names": ["time spiral"],
                "symbols": ["spiral", "time symbol"]
            },
            "time spiral remastered": {
                "codes": ["tsr"],
                "names": ["time spiral remastered"],
                "symbols": ["spiral", "remastered", "time symbol"]
            }
        }
        
        # Create reverse lookup: set_code -> expected symbols
        self.code_to_symbols = {}
        self.name_to_symbols = {}
        
        for set_key, set_info in self.symbol_patterns.items():
            for code in set_info["codes"]:
                self.code_to_symbols[code.lower()] = set_info["symbols"]
            for name in set_info["names"]:
                self.name_to_symbols[name.lower()] = set_info["symbols"]
    
    def validate_symbol_description(self, set_name: str, set_code: str, symbol_description: str) -> Tuple[bool, float, str]:
        """
        Validate if the AI's symbol description matches the expected set symbol
        
        Returns:
            (is_valid, confidence_modifier, explanation)
        """
        if not symbol_description:
            return False, -0.2, "No symbol description provided"
        
        symbol_desc_lower = symbol_description.lower()
        set_name_lower = set_name.lower() if set_name else ""
        set_code_lower = set_code.lower() if set_code else ""
        
        # Get expected symbols for this set
        expected_symbols = []
        
        if set_code_lower in self.code_to_symbols:
            expected_symbols.extend(self.code_to_symbols[set_code_lower])
        
        if set_name_lower in self.name_to_symbols:
            expected_symbols.extend(self.name_to_symbols[set_name_lower])
        
        if not expected_symbols:
            # Unknown set - can't validate but don't penalize
            return True, 0.0, f"Unknown set '{set_name}' - cannot validate symbol"
        
        # Check if AI description matches any expected symbol
        for expected in expected_symbols:
            if self._symbols_match(symbol_desc_lower, expected.lower()):
                return True, 0.1, f"Symbol description matches expected for {set_name}"
        
        # Symbol doesn't match - this is suspicious
        return False, -0.3, f"Symbol mismatch: AI says '{symbol_description}' but expected one of {expected_symbols} for {set_name}"
    
    def _symbols_match(self, ai_description: str, expected: str) -> bool:
        """Check if AI description matches expected symbol description"""
        # Clean descriptions
        ai_clean = re.sub(r'[^\w\s]', '', ai_description).strip()
        expected_clean = re.sub(r'[^\w\s]', '', expected).strip()
        
        # Exact match
        if ai_clean == expected_clean:
            return True
        
        # Partial match - check if key words overlap
        ai_words = set(ai_clean.split())
        expected_words = set(expected_clean.split())
        
        # Need at least 50% word overlap for longer descriptions
        if len(expected_words) > 1:
            overlap = len(ai_words & expected_words)
            return overlap >= len(expected_words) * 0.5
        
        # For single word descriptions, check if AI description contains the word
        return expected_clean in ai_clean or ai_clean in expected_clean
    
    def get_confidence_adjustment(self, card_data: Dict) -> Tuple[float, List[str]]:
        """
        Calculate confidence adjustment based on symbol correlation
        
        Returns:
            (confidence_adjustment, list_of_issues)
        """
        issues = []
        total_adjustment = 0.0
        
        set_name = card_data.get('set_name', '').strip()
        set_code = card_data.get('set_code', '').strip()
        symbol_desc = card_data.get('set_symbol_description', '').strip()
        
        if symbol_desc and (set_name or set_code):
            is_valid, adjustment, explanation = self.validate_symbol_description(
                set_name, set_code, symbol_desc
            )
            
            total_adjustment += adjustment
            
            if not is_valid:
                issues.append(f"Set symbol validation: {explanation}")
            elif adjustment > 0:
                issues.append(f"Set symbol confirmed: {explanation}")
        
        return total_adjustment, issues 