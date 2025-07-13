#!/usr/bin/env python3
"""
Script to delete all cards except the most recent Mishra's Factory
"""

import requests
import json
import sys

def get_all_cards():
    """Get all cards from the API"""
    try:
        response = requests.get("http://localhost:8000/cards")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching cards: {e}")
        return None

def delete_card(card_id):
    """Delete a specific card by ID"""
    try:
        response = requests.delete(f"http://localhost:8000/cards/{card_id}")
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error deleting card {card_id}: {e}")
        return False

def main():
    print("🗑️  Starting card deletion process...")
    
    # Get all cards
    data = get_all_cards()
    if not data:
        print("❌ Failed to fetch cards")
        sys.exit(1)
    
    cards = data['cards']
    print(f"📊 Found {len(cards)} total cards")
    
    # Find Mishra's Factory cards
    mishras_cards = [card for card in cards if 'Mishra' in card['name']]
    print(f"🏭 Found {len(mishras_cards)} Mishra's Factory cards")
    
    if not mishras_cards:
        print("❌ No Mishra's Factory found!")
        sys.exit(1)
    
    # Find the most recent Mishra's Factory (highest ID)
    most_recent_mishra = max(mishras_cards, key=lambda x: x['id'])
    print(f"✅ Most recent Mishra's Factory: ID {most_recent_mishra['id']} - {most_recent_mishra['name']}")
    
    # Find cards to delete (everything except the most recent Mishra)
    cards_to_delete = [card for card in cards if card['id'] != most_recent_mishra['id']]
    print(f"🎯 Cards to delete: {len(cards_to_delete)}")
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will delete ALL cards except the most recent Mishra's Factory!")
    print(f"   - Keeping: ID {most_recent_mishra['id']} - {most_recent_mishra['name']}")
    print(f"   - Deleting: {len(cards_to_delete)} cards")
    
    confirm = input("\nAre you sure you want to proceed? (type 'DELETE' to confirm): ")
    if confirm != 'DELETE':
        print("❌ Operation cancelled")
        sys.exit(0)
    
    # Delete cards
    print(f"\n🗑️  Deleting {len(cards_to_delete)} cards...")
    deleted_count = 0
    failed_count = 0
    
    for i, card in enumerate(cards_to_delete, 1):
        print(f"  [{i}/{len(cards_to_delete)}] Deleting ID {card['id']} - {card['name']}")
        
        if delete_card(card['id']):
            deleted_count += 1
        else:
            failed_count += 1
    
    print(f"\n✅ Deletion complete!")
    print(f"   - Successfully deleted: {deleted_count} cards")
    print(f"   - Failed to delete: {failed_count} cards")
    print(f"   - Remaining: 1 card (Mishra's Factory)")
    
    # Verify final state
    final_data = get_all_cards()
    if final_data:
        final_cards = final_data['cards']
        print(f"\n📊 Final verification: {len(final_cards)} cards remaining")
        for card in final_cards:
            print(f"   - ID {card['id']}: {card['name']}")

if __name__ == "__main__":
    main() 