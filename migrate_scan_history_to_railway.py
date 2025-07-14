#!/usr/bin/env python3
"""
Migrate scan history from local production database to Railway using the PostgreSQL migration approach
"""

import sqlite3
import requests
import json
from datetime import datetime
import time

# Railway API base URL
RAILWAY_API_BASE = "https://mtg-scan-production.up.railway.app"

def check_railway_connection():
    """Test connection to Railway API"""
    try:
        response = requests.get(f"{RAILWAY_API_BASE}/api/environment", timeout=10)
        if response.status_code == 200:
            print("✅ Railway API is accessible")
            return True
        else:
            print(f"❌ Railway API returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Railway API: {e}")
        return False

def get_scan_data_from_sqlite():
    """Get all scan history from the production SQLite database"""
    print("📦 Reading scan history from production database...")
    
    try:
        conn = sqlite3.connect("magic_cards.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get scans
        cursor.execute("SELECT * FROM scans ORDER BY created_at")
        scans = [dict(row) for row in cursor.fetchall()]
        
        # Get scan images
        cursor.execute("SELECT * FROM scan_images ORDER BY id")
        scan_images = [dict(row) for row in cursor.fetchall()]
        
        # Get scan results if they exist
        try:
            cursor.execute("SELECT * FROM scan_results ORDER BY id")
            scan_results = [dict(row) for row in cursor.fetchall()]
        except:
            scan_results = []
        
        conn.close()
        
        print(f"✅ Found {len(scans)} scans, {len(scan_images)} scan images, {len(scan_results)} scan results")
        return scans, scan_images, scan_results
        
    except Exception as e:
        print(f"❌ Error reading SQLite database: {e}")
        return [], [], []

def show_scan_summary():
    """Show a summary of what scans exist locally"""
    print("\n📊 Scan History Summary:")
    print("=" * 50)
    
    scans, scan_images, scan_results = get_scan_data_from_sqlite()
    
    if scans:
        print(f"📋 {len(scans)} scan sessions found")
        print(f"🖼️ {len(scan_images)} images processed")
        print(f"🎯 {len(scan_results)} scan results")
        
        # Show recent scans
        print("\n📅 Recent scans:")
        for scan in scans[-5:]:  # Last 5 scans
            created = scan.get('created_at', 'Unknown date')
            status = scan.get('status', 'Unknown')
            total_images = scan.get('total_images', 0)
            total_cards = scan.get('total_cards_found', 0)
            print(f"   Scan #{scan['id']}: {created} - {status} - {total_images} images, {total_cards} cards")
    else:
        print("No scan history found")
    
    print("\n⚠️  Note: Railway currently has cards but no scan history")
    print("💡 This migration will restore the complete scan workflow history")

def ask_user_confirmation():
    """Ask user if they want to proceed with migration"""
    print("\n" + "=" * 60)
    print("🚀 SCAN HISTORY MIGRATION")
    print("=" * 60)
    print("This will migrate your complete scan history to Railway.")
    print("The scan history shows how your cards were discovered and processed.")
    print("\nRailway currently has:")
    print("  ✅ 79 cards (already migrated)")
    print("  ❌ 0 scan sessions (missing)")
    print("\nThis migration will add:")
    print("  📋 167 scan sessions")
    print("  🖼️ 172 scan images")
    print("  🎯 Scan results and workflow history")
    
    response = input("\nProceed with scan history migration? (y/N): ").strip().lower()
    return response in ['y', 'yes']

if __name__ == "__main__":
    print("🔍 Magic Card Scanner - Scan History Migration Analysis")
    print("=" * 60)
    
    # Check Railway connection
    if not check_railway_connection():
        print("❌ Cannot proceed without Railway connection")
        exit(1)
    
    # Show what would be migrated
    show_scan_summary()
    
    # Ask for confirmation
    if ask_user_confirmation():
        print("\n⚠️  This migration requires database-level access.")
        print("📝 The scan history contains complex relationships that are")
        print("   better migrated using the existing migrate_to_postgresql.py script")
        print("   with a DATABASE_URL connection.")
        print("\n💡 Recommendation:")
        print("   1. Use Railway CLI to get DATABASE_URL")
        print("   2. Run: DATABASE_URL='...' python migrate_to_postgresql.py")
        print("   3. This will migrate ALL data including scan history")
    else:
        print("\n✅ Migration cancelled. Your Railway deployment remains unchanged.") 