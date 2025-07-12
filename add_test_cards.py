#!/usr/bin/env python3
"""
Script to add test Magic card data with real images
"""

import requests
import json
from datetime import datetime

def get_card_data(card_name):
    """Get card data from Scryfall API"""
    try:
        url = f"https://api.scryfall.com/cards/named"
        params = {"fuzzy": card_name}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting data for {card_name}: {e}")
        return None

def add_test_cards():
    """Add test cards to the database"""
    test_cards = [
        "Lightning Bolt",
        "Counterspell", 
        "Serra Angel",
        "Shivan Dragon",
        "Black Lotus",
        "Ancestral Recall",
        "Time Walk",
        "Mox Sapphire",
        "Mox Jet",
        "Mox Pearl"
    ]
    
    for card_name in test_cards:
        print(f"Adding {card_name}...")
        
        # Get real card data from Scryfall
        card_data = get_card_data(card_name)
        if not card_data:
            continue
            
        # Prepare card data for our database
        card = {
            "name": card_data.get("name", card_name),
            "set_code": card_data.get("set", "UNK"),
            "set_name": card_data.get("set_name", "Unknown"),
            "collector_number": card_data.get("collector_number", ""),
            "rarity": card_data.get("rarity", "Unknown"),
            "type_line": card_data.get("type_line", ""),
            "mana_cost": card_data.get("mana_cost", ""),
            "oracle_text": card_data.get("oracle_text", ""),
            "power": card_data.get("power", ""),
            "toughness": card_data.get("toughness", ""),
            "colors": ",".join(card_data.get("colors", [])),
            "image_url": card_data.get("image_uris", {}).get("normal", ""),
            "price_usd": float(card_data.get("prices", {}).get("usd", 0)) if card_data.get("prices", {}).get("usd") else 0.0,
            "price_eur": float(card_data.get("prices", {}).get("eur", 0)) if card_data.get("prices", {}).get("eur") else 0.0,
            "price_tix": float(card_data.get("prices", {}).get("tix", 0)) if card_data.get("prices", {}).get("tix") else 0.0,
            "count": 1,
            "condition": "NM",
            "is_example": True,
            "notes": "Test card for demonstration purposes",
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat()
        }
        
        # Add to database
        try:
            response = requests.post("http://localhost:8000/cards", json=card)
            if response.status_code == 200:
                print(f"✅ Added {card_name}")
            else:
                print(f"❌ Failed to add {card_name}: {response.text}")
        except Exception as e:
            print(f"❌ Error adding {card_name}: {e}")

if __name__ == "__main__":
    print("Adding test Magic cards to database...")
    add_test_cards()
    print("Done!") 