import requests
import json
from typing import Optional, Dict, Any

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
            print(f"Error searching for card {card_name}: {e}")
            return None
    
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
    def get_card_data(card_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive card data including prices"""
        card_data = ScryfallAPI.search_card(card_name)
        if not card_data:
            return None
        
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
            "image_url": card_data.get("image_uris", {}).get("normal"),
            "price_usd": float(card_data.get("prices", {}).get("usd", 0)) if card_data.get("prices", {}).get("usd") else 0.0,
            "price_eur": float(card_data.get("prices", {}).get("eur", 0)) if card_data.get("prices", {}).get("eur") else 0.0,
            "price_tix": float(card_data.get("prices", {}).get("tix", 0)) if card_data.get("prices", {}).get("tix") else 0.0
        } 