import requests
import json
from typing import Optional, Dict, Any, List
import re

class ScryfallAPI:
    """Interface for Scryfall API to get card data and prices"""
    
    BASE_URL = "https://api.scryfall.com"
    
    @staticmethod
    def search_card(card_name: str) -> Optional[Dict[str, Any]]:
        """Search for a card by name"""
        try:
            url = f"{ScryfallAPI.BASE_URL}/cards/named"
            params = {"fuzzy": card_name}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # For non-English card names, try to find English equivalent
            if hasattr(e, 'response') and e.response and e.response.status_code == 404:
                print(f"Card not found in English: {card_name} (possibly non-English name)")
            else:
                print(f"Error searching for card {card_name}: {e}")
            return None
    
    @staticmethod
    def search_card_with_set(card_name: str, set_code: Optional[str] = None, set_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Search for a card with specific set information"""
        try:
            # Try exact set code first if provided
            if set_code:
                url = f"{ScryfallAPI.BASE_URL}/cards/named"
                params = {"fuzzy": card_name, "set": set_code}
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    return response.json()
            
            # Try searching all printings and filter by set name
            if set_name:
                url = f"{ScryfallAPI.BASE_URL}/cards/search"
                # Use exact name search with set filter
                params = {"q": f'name:"{card_name}" set:"{set_name}"'}
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        return data['data'][0]  # Return first match
            
            # Fallback to fuzzy search if set-specific search fails
            return ScryfallAPI.search_card(card_name)
            
        except requests.RequestException as e:
            set_info = set_code or set_name or "unknown"
            print(f"Error searching for card {card_name} with set {set_info}: {e}")
            return ScryfallAPI.search_card(card_name)
    
    @staticmethod
    def get_all_printings(card_name: str) -> List[Dict[str, Any]]:
        """Get all printings of a card"""
        try:
            url = f"{ScryfallAPI.BASE_URL}/cards/search"
            params = {"q": f'name:"{card_name}"'}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.RequestException as e:
            print(f"Error getting all printings for {card_name}: {e}")
            return []
    
    @staticmethod
    def find_best_match(card_name: str, ai_set_info: Optional[str] = None, prefer_modern: bool = True) -> Optional[Dict[str, Any]]:
        """Find the best matching card using multiple strategies"""
        
        # Strategy 1: Use AI-provided set information if available
        if ai_set_info:
            # Clean and parse AI set information
            ai_set_clean = ai_set_info.strip().lower()
            
            # Try common set name patterns
            set_patterns = [
                ai_set_clean,
                ai_set_clean.replace(" ", ""),
                ai_set_clean.replace("-", ""),
                ai_set_clean.replace("'", ""),
            ]
            
            for pattern in set_patterns:
                result = ScryfallAPI.search_card_with_set(card_name, set_name=pattern)
                if result:
                    return result
        
        # Strategy 2: Get all printings and use smart selection
        all_printings = ScryfallAPI.get_all_printings(card_name)
        if not all_printings:
            return ScryfallAPI.search_card(card_name)
        
        # Strategy 3: Smart selection based on preferences
        if prefer_modern:
            # Prefer newer sets and avoid very old/expensive reprints
            preferred_sets = ['neo', 'snc', 'dmu', 'bro', 'one', 'mom', 'ltr', 'woe', 'lci', 'mkm', 'otj', 'mh3', 'blb', 'dsk', 'fdn']
            
            for printing in all_printings:
                if printing.get('set') in preferred_sets:
                    return printing
            
            # If no preferred modern sets, get most recent non-premium set
            standard_printings = [p for p in all_printings if not ScryfallAPI._is_premium_set(p.get('set', ''))]
            if standard_printings:
                # Sort by release date descending
                standard_printings.sort(key=lambda x: x.get('released_at', ''), reverse=True)
                return standard_printings[0]
        
        # Strategy 4: Return first available printing
        return all_printings[0] if all_printings else None
    
    @staticmethod
    def _is_premium_set(set_code: str) -> bool:
        """Check if a set is premium/expensive (avoid these for default selection)"""
        premium_sets = ['lea', 'leb', 'arn', 'atq', 'leg', 'drk', 'fem', 'ice', 'all', 'hml', 'mir', 'vis', 'wth', 'tmp', 'sth', 'exo', 'usg', 'ulg', 'uds', 'mmq', 'nem', 'pcy', 'inv', 'pls', 'apc', 'ody', 'tor', 'jud', 'ons', 'lgn', 'scg', 'mrd', 'dst', 'fifth', 'rav', 'gpt', 'dis', 'csp', 'tsp', 'plc', 'fut', 'lrw', 'mor', 'shm', 'eve', 'ala', 'con', 'arb', 'zen', 'wwk', 'roe', 'som', 'mbs', 'nph', 'isd', 'dka', 'avr', 'rtr', 'gtc', 'dgm', 'ths', 'bng', 'jou', 'ktk', 'frf', 'dtk', 'ori', 'bfz', 'ogw', 'soi', 'emn', 'kld', 'aer', 'akh', 'hou', 'xln', 'rix', 'dom', 'rna', 'war', 'eldm', 'thb', 'iko', 'znr', 'khm', 'stx', 'afr', 'mid', 'vow', 'vow']
        return set_code.lower() in premium_sets
    
    @staticmethod
    def get_card_by_name(card_name: str) -> Optional[Dict[str, Any]]:
        """Get exact card by name"""
        try:
            url = f"{ScryfallAPI.BASE_URL}/cards/named"
            params = {"exact": card_name}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting card {card_name}: {e}")
            return None
    
    @staticmethod
    def get_card_prices(card_name: str) -> Dict[str, float]:
        """Get current prices for a card"""
        card_data = ScryfallAPI.search_card(card_name)
        if not card_data:
            return {"usd": 0.0, "eur": 0.0, "tix": 0.0}
        
        prices = {
            "usd": card_data.get("prices", {}).get("usd", 0.0),
            "eur": card_data.get("prices", {}).get("eur", 0.0),
            "tix": card_data.get("prices", {}).get("tix", 0.0)
        }
        
        # Convert string prices to float
        for currency in prices:
            if isinstance(prices[currency], str):
                try:
                    prices[currency] = float(prices[currency]) if prices[currency] else 0.0
                except ValueError:
                    prices[currency] = 0.0
        
        return prices
    
    @staticmethod
    def get_card_data(card_name: str, ai_set_info: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get comprehensive card data including prices with smart set selection"""
        
        # Use deterministic search for consistency
        card_data = ScryfallAPI.search_card_deterministic(card_name)
        
        # If we have AI set info, try to find a better match with that set
        if card_data and ai_set_info:
            set_specific_card = ScryfallAPI.find_best_match(card_name, ai_set_info)
            if set_specific_card:
                card_data = set_specific_card
        
        if not card_data:
            return None
        
        # Extract prices safely
        prices = card_data.get("prices", {})
        price_usd = 0.0
        price_eur = 0.0
        price_tix = 0.0
        
        if prices.get("usd"):
            try:
                price_usd = float(prices["usd"])
            except (ValueError, TypeError):
                price_usd = 0.0
        
        if prices.get("eur"):
            try:
                price_eur = float(prices["eur"])
            except (ValueError, TypeError):
                price_eur = 0.0
        
        if prices.get("tix"):
            try:
                price_tix = float(prices["tix"])
            except (ValueError, TypeError):
                price_tix = 0.0
        
        # Get the correct image URL
        image_url = ""
        image_uris = card_data.get("image_uris", {})
        if image_uris:
            # Prefer normal size, fallback to small, then large
            image_url = image_uris.get("normal", image_uris.get("small", image_uris.get("large", "")))
        
        return {
            "name": card_data.get("name"),
            "set_code": card_data.get("set"),
            "set_name": card_data.get("set_name"),
            "collector_number": card_data.get("collector_number"),
            "rarity": card_data.get("rarity"),
            "mana_cost": card_data.get("mana_cost"),
            "type_line": card_data.get("type_line"),
            "oracle_text": card_data.get("oracle_text"),
            "flavor_text": card_data.get("flavor_text"),
            "power": card_data.get("power"),
            "toughness": card_data.get("toughness"),
            "colors": ",".join(card_data.get("colors", [])),
            "image_url": image_url,
            "price_usd": price_usd,
            "price_eur": price_eur,
            "price_tix": price_tix
        }
    
    @staticmethod
    def populate_missing_set_data(card_name: str, current_set_code: Optional[str] = None) -> Dict[str, Any]:
        """Populate missing set data for existing cards"""
        if current_set_code:
            # Try to get more complete data for the current set
            card_data = ScryfallAPI.search_card_with_set(card_name, set_code=current_set_code)
            if card_data:
                return {
                    "set_name": card_data.get("set_name", ""),
                    "collector_number": card_data.get("collector_number", ""),
                    "rarity": card_data.get("rarity", ""),
                    "image_url": card_data.get("image_uris", {}).get("normal", "")
                }
        
        # Fallback to default search
        card_data = ScryfallAPI.search_card(card_name)
        if card_data:
            return {
                "set_name": card_data.get("set_name", ""),
                "collector_number": card_data.get("collector_number", ""),
                "rarity": card_data.get("rarity", ""),
                "image_url": card_data.get("image_uris", {}).get("normal", "")
            }
        
        return {} 

    @staticmethod
    def search_card_deterministic(card_name: str) -> Optional[Dict[str, Any]]:
        """Search for a card with deterministic results (no fuzzy matching randomness)"""
        try:
            # Strategy 1: Try exact name match first
            url = f"{ScryfallAPI.BASE_URL}/cards/named"
            params = {"exact": card_name}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            
            # Strategy 2: Try fuzzy search but use a consistent selection strategy
            params = {"fuzzy": card_name}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            
            # Strategy 3: Search all printings and pick the most recent/stable version
            search_url = f"{ScryfallAPI.BASE_URL}/cards/search"
            search_params = {"q": f'name:"{card_name}"', "order": "released", "dir": "desc"}
            response = requests.get(search_url, params=search_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                cards = data.get('data', [])
                if cards:
                    # Return the most recent printing for consistency
                    return cards[0]
            
            return None
            
        except requests.RequestException as e:
            print(f"Error searching for card {card_name}: {e}")
            return None 