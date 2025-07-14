#!/usr/bin/env python3
"""
Scan-Card Relationship Check

Check how scans reference the cards they found:
1. Does the scan table store card IDs directly?
2. Or is it through foreign key relationships?
"""

import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import inspect

# Add the project root to the path so we can import from backend
sys.path.append('.')

from backend.database import get_db, Card, Scan, ScanImage, ScanResult

def check_scan_card_relationships():
    """Check how scans reference their found cards"""
    print("=" * 80)
    print("🔍 SCAN-CARD RELATIONSHIP STRUCTURE")
    print("=" * 80)
    
    db = next(get_db())
    
    # First, let's look at what columns the Scan table actually has
    print("\n📋 SCAN TABLE COLUMNS:")
    inspector = inspect(db.bind)
    scan_columns = inspector.get_columns('scans')
    for col in scan_columns:
        print(f"   {col['name']}: {col['type']}")
    
    # Check if Scan has any card_ids field or similar
    scan_column_names = [col['name'] for col in scan_columns]
    has_card_ids = any('card' in name.lower() and 'id' in name.lower() for name in scan_column_names)
    print(f"\n❓ Does Scan table have card ID fields? {'YES' if has_card_ids else 'NO'}")
    
    # Now let's examine a specific scan and see how it accesses its cards
    print(f"\n🔍 EXAMINING SCAN #163 (largest scan with 21 cards):")
    
    scan_163 = db.query(Scan).filter(Scan.id == 163).first()
    if scan_163:
        print(f"   Scan ID: {scan_163.id}")
        print(f"   Total Cards Found: {scan_163.total_cards_found}")
        
        # Method 1: Through the SQLAlchemy relationship
        print(f"\n   📝 METHOD 1 - Via SQLAlchemy relationship:")
        try:
            related_cards = scan_163.cards  # This uses the relationship
            print(f"   scan_163.cards found: {len(related_cards)} cards")
            for i, card in enumerate(related_cards[:3], 1):  # Show first 3
                print(f"      {i}. Card #{card.id}: {card.name}")
            if len(related_cards) > 3:
                print(f"      ... and {len(related_cards) - 3} more")
        except Exception as e:
            print(f"   Error with relationship: {e}")
        
        # Method 2: Through direct query using foreign key
        print(f"\n   📝 METHOD 2 - Via foreign key query:")
        cards_by_scan_id = db.query(Card).filter(
            Card.scan_id == 163
        ).filter(
            Card.deleted.is_(False)
        ).all()
        print(f"   Direct query found: {len(cards_by_scan_id)} cards")
        
        # Method 3: Through scan results
        print(f"\n   📝 METHOD 3 - Via scan results:")
        scan_results = db.query(ScanResult).filter(ScanResult.scan_id == 163).all()
        print(f"   Scan results found: {len(scan_results)}")
        
        cards_via_results = []
        for result in scan_results:
            card = db.query(Card).filter(
                Card.scan_result_id == result.id
            ).filter(
                Card.deleted.is_(False)
            ).first()
            if card:
                cards_via_results.append(card)
        
        print(f"   Cards via scan results: {len(cards_via_results)}")
        
        # Compare the methods
        print(f"\n   🔍 COMPARISON:")
        print(f"   Method 1 (relationship): {len(related_cards) if 'related_cards' in locals() else 'N/A'}")
        print(f"   Method 2 (scan_id FK):    {len(cards_by_scan_id)}")
        print(f"   Method 3 (via results):   {len(cards_via_results)}")
        
        # Check if scan stores any direct references
        print(f"\n   📋 SCAN RECORD DETAILS:")
        for attr in ['id', 'total_cards_found', 'total_images', 'status']:
            if hasattr(scan_163, attr):
                print(f"   {attr}: {getattr(scan_163, attr)}")
    
    print(f"\n" + "=" * 80)
    print("🎯 CONCLUSION:")
    print("   The Scan table does NOT store card IDs directly.")
    print("   Cards reference scans via:")
    print("   1. card.scan_id → scan.id (foreign key)")
    print("   2. card.scan_result_id → scan_result.id → scan_result.scan_id")
    print("   3. SQLAlchemy relationships handle the connections")
    print("=" * 80)

if __name__ == "__main__":
    check_scan_card_relationships() 