#!/usr/bin/env python3
"""
Script to update card images and data from Scryfall API
"""

import requests
import sqlite3
import time
import json

def fetch_card_data(card_name):
    """Fetch card data from Scryfall API"""
    try:
        # Search for the card
        search_url = f"https://api.scryfall.com/cards/search?q={card_name}"
        response = requests.get(search_url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                card = data['data'][0]  # Get the first result
                
                # Extract relevant data
                return {
                    'name': card.get('name', card_name),
                    'image_url': card.get('image_uris', {}).get('normal', ''),
                    'price_usd': float(card.get('prices', {}).get('usd', 0) or 0),
                    'price_eur': float(card.get('prices', {}).get('eur', 0) or 0),
                    'set_code': card.get('set', ''),
                    'set_name': card.get('set_name', ''),
                    'collector_number': card.get('collector_number', ''),
                    'rarity': card.get('rarity', ''),
                    'mana_cost': card.get('mana_cost', ''),
                    'type_line': card.get('type_line', ''),
                    'oracle_text': card.get('oracle_text', ''),
                    'power': card.get('power', ''),
                    'toughness': card.get('toughness', ''),
                    'colors': ','.join(card.get('colors', []))
                }
    except Exception as e:
        print(f"Error fetching data for {card_name}: {e}")
    
    return None

def update_database():
    """Update the database with real card data"""
    conn = sqlite3.connect('magic_cards.db')
    cursor = conn.cursor()
    
    # Get all cards from database
    cursor.execute('SELECT id, name FROM cards')
    cards = cursor.fetchall()
    
    print(f"Found {len(cards)} cards to update...")
    
    updated_count = 0
    for card_id, card_name in cards:
        print(f"Updating {card_name}...")
        
        card_data = fetch_card_data(card_name)
        if card_data:
            # Update the card in database
            cursor.execute('''
                UPDATE cards SET 
                    image_url = ?, price_usd = ?, price_eur = ?, 
                    set_code = ?, set_name = ?, collector_number = ?,
                    rarity = ?, mana_cost = ?, type_line = ?, 
                    oracle_text = ?, power = ?, toughness = ?, colors = ?
                WHERE id = ?
            ''', (
                card_data['image_url'], card_data['price_usd'], card_data['price_eur'],
                card_data['set_code'], card_data['set_name'], card_data['collector_number'],
                card_data['rarity'], card_data['mana_cost'], card_data['type_line'],
                card_data['oracle_text'], card_data['power'], card_data['toughness'],
                card_data['colors'], card_id
            ))
            updated_count += 1
            print(f"  ✓ Updated {card_name}")
        else:
            print(f"  ✗ Failed to update {card_name}")
        
        # Be nice to the API
        time.sleep(0.1)
    
    conn.commit()
    conn.close()
    
    print(f"\nUpdated {updated_count} cards successfully!")

if __name__ == "__main__":
    print("Updating card images and data from Scryfall API...")
    update_database() 