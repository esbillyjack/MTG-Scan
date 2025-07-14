#!/usr/bin/env python3
"""
Scan Data Integrity Report

This script generates a comprehensive report showing:
1. Each scan and its discovered cards
2. Whether those cards still exist in the database with the same ID
3. File existence for scan images
4. Data integrity between scans and cards
"""

import os
import sys
from sqlalchemy.orm import Session
from datetime import datetime

# Add the project root to the path so we can import from backend
sys.path.append('.')

from backend.database import get_db, Card, Scan, ScanImage, ScanResult

def check_file_exists(filename):
    """Check if a scan image file exists locally"""
    file_path = os.path.join("uploads", filename)
    return os.path.exists(file_path)

def generate_scan_integrity_report():
    """Generate a comprehensive scan data integrity report"""
    print("=" * 80)
    print("🔍 SCAN DATA INTEGRITY REPORT")
    print("=" * 80)
    print(f"Generated at: {datetime.now().isoformat()}")
    print()
    
    db = next(get_db())
    
    # Get all scans, ordered by ID
    scans = db.query(Scan).order_by(Scan.id).all()
    
    print(f"📊 SUMMARY:")
    print(f"   Total Scans: {len(scans)}")
    
    total_scan_results = db.query(ScanResult).count()
    total_cards = db.query(Card).filter(Card.deleted.is_(False)).count()
    total_cards_from_scans = db.query(Card).filter(Card.scan_id.isnot(None)).filter(Card.deleted.is_(False)).count()
    
    print(f"   Total Scan Results: {total_scan_results}")
    print(f"   Total Cards in DB: {total_cards}")
    print(f"   Cards from Scans: {total_cards_from_scans}")
    print()
    
    # Track integrity stats
    integrity_stats = {
        'scans_with_results': 0,
        'scan_results_total': 0,
        'scan_results_accepted': 0,
        'scan_results_with_cards': 0,
        'scan_results_orphaned': 0,
        'images_with_files': 0,
        'images_missing_files': 0,
        'cards_with_scan_links': 0,
        'cards_orphaned_from_scans': 0
    }
    
    print("🔍 DETAILED SCAN ANALYSIS:")
    print("-" * 80)
    
    for scan in scans:
        print(f"\n📋 SCAN #{scan.id}")
        print(f"   Created: {scan.created_at}")
        print(f"   Status: {scan.status}")
        print(f"   Images: {scan.total_images} | Processed: {scan.processed_images}")
        print(f"   Cards Found: {scan.total_cards_found}")
        
        # Get scan images
        scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan.id).all()
        print(f"   📁 Scan Images ({len(scan_images)}):")
        
        for img in scan_images:
            file_exists = check_file_exists(img.filename)
            status_icon = "✅" if file_exists else "❌"
            print(f"      {status_icon} {img.filename} (cards: {img.cards_found})")
            
            if file_exists:
                integrity_stats['images_with_files'] += 1
            else:
                integrity_stats['images_missing_files'] += 1
        
        # Get scan results
        scan_results = db.query(ScanResult).filter(ScanResult.scan_id == scan.id).all()
        integrity_stats['scan_results_total'] += len(scan_results)
        
        if scan_results:
            integrity_stats['scans_with_results'] += 1
            
        print(f"   🎯 Scan Results ({len(scan_results)}):")
        
        for result in scan_results:
            integrity_stats['scan_results_accepted'] += (1 if result.status == 'ACCEPTED' else 0)
            
            # Check if there's a corresponding card
            card = db.query(Card).filter(
                Card.scan_result_id == result.id
            ).filter(
                Card.deleted.is_(False)
            ).first()
            
            card_exists = "✅" if card else "❌"
            card_info = f"Card ID: {card.id}" if card else "NO CARD"
            
            if card:
                integrity_stats['scan_results_with_cards'] += 1
                integrity_stats['cards_with_scan_links'] += 1
            else:
                integrity_stats['scan_results_orphaned'] += 1
            
            print(f"      {card_exists} {result.card_name} [{result.status}] → {card_info}")
            
            # Additional details for accepted results without cards
            if result.status == 'ACCEPTED' and not card:
                print(f"         ⚠️  ACCEPTED result but NO corresponding card!")
    
    # Check for orphaned cards (cards that reference non-existent scans/results)
    print(f"\n🔍 ORPHANED CARDS ANALYSIS:")
    print("-" * 80)
    
    orphaned_cards = db.query(Card).filter(
        Card.scan_id.isnot(None)
    ).filter(
        Card.deleted.is_(False)
    ).all()
    
    for card in orphaned_cards:
        # Check if the referenced scan exists
        scan_exists = db.query(Scan).filter(Scan.id == card.scan_id).first() is not None
        
        # Check if the referenced scan result exists
        result_exists = True
        if card.scan_result_id:
            result_exists = db.query(ScanResult).filter(ScanResult.id == card.scan_result_id).first() is not None
        
        if not scan_exists or not result_exists:
            integrity_stats['cards_orphaned_from_scans'] += 1
            print(f"   ⚠️  Card #{card.id} '{card.name}' references:")
            print(f"      Scan #{card.scan_id}: {'✅' if scan_exists else '❌ MISSING'}")
            if card.scan_result_id:
                print(f"      Result #{card.scan_result_id}: {'✅' if result_exists else '❌ MISSING'}")
    
    # Final integrity summary
    print(f"\n📊 INTEGRITY SUMMARY:")
    print("=" * 80)
    print(f"✅ Scans with Results: {integrity_stats['scans_with_results']}/{len(scans)}")
    print(f"✅ Scan Results Total: {integrity_stats['scan_results_total']}")
    print(f"✅ Scan Results Accepted: {integrity_stats['scan_results_accepted']}")
    print(f"✅ Results with Cards: {integrity_stats['scan_results_with_cards']}")
    print(f"❌ Orphaned Results: {integrity_stats['scan_results_orphaned']}")
    print(f"✅ Images with Files: {integrity_stats['images_with_files']}")
    print(f"❌ Images Missing Files: {integrity_stats['images_missing_files']}")
    print(f"✅ Cards with Scan Links: {integrity_stats['cards_with_scan_links']}")
    print(f"❌ Cards Orphaned: {integrity_stats['cards_orphaned_from_scans']}")
    
    # Calculate integrity percentages
    if integrity_stats['scan_results_total'] > 0:
        result_integrity = (integrity_stats['scan_results_with_cards'] / integrity_stats['scan_results_total']) * 100
        print(f"\n📈 INTEGRITY METRICS:")
        print(f"   Scan Result → Card Integrity: {result_integrity:.1f}%")
    
    total_images = integrity_stats['images_with_files'] + integrity_stats['images_missing_files']
    if total_images > 0:
        file_integrity = (integrity_stats['images_with_files'] / total_images) * 100
        print(f"   File Availability: {file_integrity:.1f}%")
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS:")
    
    if integrity_stats['scan_results_orphaned'] > 0:
        print(f"   • {integrity_stats['scan_results_orphaned']} scan results don't have corresponding cards")
    
    if integrity_stats['images_missing_files'] > 0:
        print(f"   • {integrity_stats['images_missing_files']} scan images are missing files")
    
    if integrity_stats['cards_orphaned_from_scans'] > 0:
        print(f"   • {integrity_stats['cards_orphaned_from_scans']} cards reference non-existent scans/results")
        
    print("=" * 80)

if __name__ == "__main__":
    generate_scan_integrity_report() 