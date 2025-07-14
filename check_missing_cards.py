#!/usr/bin/env python3
"""
Check Missing Cards Investigation

Check if Lightning Bolt and Forcefield cards actually exist and what their scan associations are.
"""

import os
import sys
from sqlalchemy.orm import Session

# Add the project root to the path so we can import from backend
sys.path.append('.')

from backend.database import get_db, Card, Scan, ScanImage, ScanResult

def check_missing_cards():
    """Check the specific cards that the report said were missing"""
    print("=" * 80)
    print("🔍 INVESTIGATING 'MISSING' CARDS")
    print("=" * 80)
    
    db = next(get_db())
    
    # Check for Lightning Bolt cards
    print("\n🔍 LIGHTNING BOLT CARDS:")
    lightning_bolts = db.query(Card).filter(
        Card.name == 'Lightning Bolt'
    ).filter(
        Card.deleted.is_(False)
    ).all()
    
    print(f"Found {len(lightning_bolts)} Lightning Bolt cards:")
    for card in lightning_bolts:
        print(f"   Card #{card.id}: scan_id={card.scan_id}, scan_result_id={card.scan_result_id}")
        
        # Check what scan result this points to
        if card.scan_result_id:
            result = db.query(ScanResult).filter(ScanResult.id == card.scan_result_id).first()
            if result:
                print(f"      → Points to Result #{result.id} from Scan #{result.scan_id}")
            else:
                print(f"      → Points to MISSING Result #{card.scan_result_id}")
    
    # Check for Forcefield cards  
    print("\n🔍 FORCEFIELD CARDS:")
    forcefields = db.query(Card).filter(
        Card.name == 'Forcefield'
    ).filter(
        Card.deleted.is_(False)
    ).all()
    
    print(f"Found {len(forcefields)} Forcefield cards:")
    for card in forcefields:
        print(f"   Card #{card.id}: scan_id={card.scan_id}, scan_result_id={card.scan_result_id}")
        
        # Check what scan result this points to
        if card.scan_result_id:
            result = db.query(ScanResult).filter(ScanResult.id == card.scan_result_id).first()
            if result:
                print(f"      → Points to Result #{result.id} from Scan #{result.scan_id}")
            else:
                print(f"      → Points to MISSING Result #{card.scan_result_id}")
    
    # Now check the specific scan results that the report said had no cards
    print("\n🔍 CHECKING SPECIFIC 'ORPHANED' SCAN RESULTS:")
    
    # Result #714 (Lightning Bolt from Scan #139)
    print(f"\nResult #714 (Lightning Bolt from Scan #139):")
    result_714 = db.query(ScanResult).filter(ScanResult.id == 714).first()
    if result_714:
        print(f"   Result exists: {result_714.card_name} from Scan #{result_714.scan_id}")
        
        # Check if ANY card points to this result
        cards_pointing_to_714 = db.query(Card).filter(
            Card.scan_result_id == 714
        ).filter(
            Card.deleted.is_(False)
        ).all()
        print(f"   Cards pointing to this result: {len(cards_pointing_to_714)}")
        for card in cards_pointing_to_714:
            print(f"      Card #{card.id}: {card.name}")
    
    # Result #721 (Forcefield from Scan #140) 
    print(f"\nResult #721 (Forcefield from Scan #140):")
    result_721 = db.query(ScanResult).filter(ScanResult.id == 721).first()
    if result_721:
        print(f"   Result exists: {result_721.card_name} from Scan #{result_721.scan_id}")
        
        # Check if ANY card points to this result
        cards_pointing_to_721 = db.query(Card).filter(
            Card.scan_result_id == 721
        ).filter(
            Card.deleted.is_(False)
        ).all()
        print(f"   Cards pointing to this result: {len(cards_pointing_to_721)}")
        for card in cards_pointing_to_721:
            print(f"      Card #{card.id}: {card.name}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_missing_cards() 