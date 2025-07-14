#!/usr/bin/env python3
"""
Detailed Scan-Card Relationship Report

This script walks through each SCAN and:
1. Lists what cards the scan thinks it found
2. Verifies if those cards still exist in the database 
3. Checks if the card's scan_id points back to the same scan
4. Shows any mismatches in the bidirectional relationship
"""

import os
import sys
from sqlalchemy.orm import Session
from datetime import datetime

# Add the project root to the path so we can import from backend
sys.path.append('.')

from backend.database import get_db, Card, Scan, ScanImage, ScanResult

def detailed_scan_card_report():
    """Generate a detailed report of scan-card relationships"""
    print("=" * 100)
    print("🔍 DETAILED SCAN-CARD RELATIONSHIP REPORT")
    print("=" * 100)
    print(f"Generated at: {datetime.now().isoformat()}")
    print()
    
    db = next(get_db())
    
    # Get all scans, ordered by ID
    scans = db.query(Scan).order_by(Scan.id).all()
    
    print(f"📊 WALKING THROUGH {len(scans)} SCANS:")
    print("=" * 100)
    
    total_mismatches = 0
    total_missing_cards = 0
    total_wrong_scan_refs = 0
    
    for scan in scans:
        print(f"\n🔍 SCAN #{scan.id}")
        print(f"   Created: {scan.created_at}")
        print(f"   Status: {scan.status}")
        print(f"   Total Cards Found: {scan.total_cards_found}")
        
        # Get what this scan thinks it found (from scan_results)
        scan_results = db.query(ScanResult).filter(ScanResult.scan_id == scan.id).order_by(ScanResult.id).all()
        
        print(f"\n   📋 SCAN SAYS IT FOUND {len(scan_results)} RESULTS:")
        print("   " + "-" * 80)
        
        if not scan_results:
            print("   (No scan results found)")
            continue
            
        for i, result in enumerate(scan_results, 1):
            print(f"   {i:2d}. {result.card_name} [{result.status}] (Result ID: {result.id})")
            
            # Check if there's a card that references this scan result
            card_from_result = db.query(Card).filter(
                Card.scan_result_id == result.id
            ).filter(
                Card.deleted.is_(False)
            ).first()
            
            if card_from_result:
                print(f"       ✅ Card exists: ID {card_from_result.id}")
                
                # Check if the card's scan_id points back to this scan
                if card_from_result.scan_id == scan.id:
                    print(f"       ✅ Card's scan_id points back correctly ({card_from_result.scan_id})")
                else:
                    print(f"       ❌ Card's scan_id WRONG: points to {card_from_result.scan_id}, should be {scan.id}")
                    total_wrong_scan_refs += 1
                    
            else:
                print(f"       ❌ FALSE - No card exists for this scan result")
                total_missing_cards += 1
                
                # If it was ACCEPTED but no card exists, that's a problem
                if result.status == 'ACCEPTED':
                    print(f"       ⚠️  WARNING: ACCEPTED result but no card!")
                    
    print(f"\n" + "=" * 100)
    print("🔄 REVERSE LOOKUP - CHECKING CARDS THAT CLAIM TO BE FROM SCANS:")
    print("=" * 100)
    
    # Get all cards that claim to be from scans
    cards_from_scans = db.query(Card).filter(
        Card.scan_id.isnot(None)
    ).filter(
        Card.deleted.is_(False)
    ).order_by(Card.scan_id, Card.id).all()
    
    print(f"\nFound {len(cards_from_scans)} cards that claim to be from scans:")
    
    current_scan_id = None
    cards_by_scan = {}
    
    # Group cards by their claimed scan_id
    for card in cards_from_scans:
        if card.scan_id not in cards_by_scan:
            cards_by_scan[card.scan_id] = []
        cards_by_scan[card.scan_id].append(card)
    
    # Check each scan's claimed cards
    for scan_id, cards in cards_by_scan.items():
        print(f"\n🔍 Cards claiming to be from SCAN #{scan_id}:")
        
        # Verify the scan exists
        scan_exists = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan_exists:
            print(f"   ❌ SCAN #{scan_id} DOES NOT EXIST!")
            total_mismatches += len(cards)
            for card in cards:
                print(f"      Card #{card.id} '{card.name}' claims non-existent scan")
            continue
            
        print(f"   ✅ Scan exists - checking {len(cards)} cards:")
        
        for card in cards:
            # Check if this scan actually has a result for this card
            if card.scan_result_id:
                scan_result = db.query(ScanResult).filter(
                    ScanResult.id == card.scan_result_id,
                    ScanResult.scan_id == scan_id
                ).first()
                
                if scan_result:
                    print(f"      ✅ Card #{card.id} '{card.name}' ↔ Result #{card.scan_result_id} ✅")
                else:
                    print(f"      ❌ Card #{card.id} '{card.name}' references Result #{card.scan_result_id} but it doesn't belong to Scan #{scan_id}")
                    total_mismatches += 1
            else:
                print(f"      ⚠️  Card #{card.id} '{card.name}' has scan_id {scan_id} but NO scan_result_id")
    
    # Summary
    print(f"\n" + "=" * 100)
    print("📊 RELATIONSHIP INTEGRITY SUMMARY:")
    print("=" * 100)
    print(f"❌ Missing Cards (ACCEPTED results with no cards): {total_missing_cards}")
    print(f"❌ Wrong Scan References (cards pointing to wrong scan): {total_wrong_scan_refs}")
    print(f"❌ Bidirectional Mismatches (scan-card disagreements): {total_mismatches}")
    
    total_issues = total_missing_cards + total_wrong_scan_refs + total_mismatches
    print(f"\n🎯 TOTAL RELATIONSHIP ISSUES: {total_issues}")
    
    if total_issues == 0:
        print("✅ All scan-card relationships are PERFECT!")
    else:
        print("⚠️  There are relationship issues that need fixing.")
    
    print("=" * 100)

if __name__ == "__main__":
    detailed_scan_card_report() 