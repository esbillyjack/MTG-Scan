#!/usr/bin/env python3
"""
Debug script to compare scan data between development and production Railway databases
"""

import os
import psycopg2
from psycopg2 import sql
import sys
from datetime import datetime

# Database connection strings
DEV_DATABASE_URL = "postgresql://postgres:NuhLRXDVKTjRQNPLdSKvPoADLSrnrsjJ@turntable.proxy.rlwy.net:12246/railway"
PROD_DATABASE_URL = "postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

def get_database_connection(database_url, db_name):
    """Get database connection"""
    try:
        conn = psycopg2.connect(database_url)
        print(f"✅ Connected to {db_name} database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to {db_name} database: {e}")
        return None

def get_scan_statistics(conn, db_name):
    """Get scan statistics from database"""
    try:
        cursor = conn.cursor()
        
        # Get total scans
        cursor.execute("SELECT COUNT(*) FROM scans;")
        total_scans = cursor.fetchone()[0]
        
        # Get scans with cards
        cursor.execute("""
            SELECT COUNT(DISTINCT s.id) 
            FROM scans s 
            WHERE s.total_cards_found > 0 
            AND s.status != 'CANCELLED';
        """)
        scans_with_cards = cursor.fetchone()[0]
        
        # Get scan images
        cursor.execute("SELECT COUNT(*) FROM scan_images;")
        total_scan_images = cursor.fetchone()[0]
        
        # Get scan results
        cursor.execute("SELECT COUNT(*) FROM scan_results;")
        total_scan_results = cursor.fetchone()[0]
        
        # Get recent scans
        cursor.execute("""
            SELECT id, status, total_cards_found, total_images, created_at
            FROM scans 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        recent_scans = cursor.fetchall()
        
        # Get cards associated with scans
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cards 
            WHERE scan_id IS NOT NULL 
            AND deleted = false;
        """)
        cards_from_scans = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            'total_scans': total_scans,
            'scans_with_cards': scans_with_cards,
            'total_scan_images': total_scan_images,
            'total_scan_results': total_scan_results,
            'recent_scans': recent_scans,
            'cards_from_scans': cards_from_scans
        }
        
    except Exception as e:
        print(f"❌ Error getting scan statistics for {db_name}: {e}")
        return None

def get_table_schemas(conn, db_name):
    """Get table schemas to compare structure"""
    try:
        cursor = conn.cursor()
        
        # Get scan-related table schemas
        tables = ['scans', 'scan_images', 'scan_results', 'cards']
        schemas = {}
        
        for table in tables:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            
            columns = cursor.fetchall()
            schemas[table] = columns
            
        cursor.close()
        return schemas
        
    except Exception as e:
        print(f"❌ Error getting table schemas for {db_name}: {e}")
        return None

def compare_scan_data():
    """Compare scan data between development and production"""
    print("🔍 Magic Card Scanner - Scan Data Comparison")
    print("=" * 60)
    
    # Connect to both databases
    dev_conn = get_database_connection(DEV_DATABASE_URL, "Development")
    prod_conn = get_database_connection(PROD_DATABASE_URL, "Production")
    
    if not dev_conn or not prod_conn:
        print("❌ Failed to connect to one or both databases")
        return
    
    try:
        # Get scan statistics
        print("\n📊 SCAN STATISTICS COMPARISON")
        print("-" * 40)
        
        dev_stats = get_scan_statistics(dev_conn, "Development")
        prod_stats = get_scan_statistics(prod_conn, "Production")
        
        if dev_stats and prod_stats:
            print(f"{'Metric':<25} {'Development':<15} {'Production':<15} {'Match':<10}")
            print("-" * 70)
            
            metrics = [
                ('Total Scans', 'total_scans'),
                ('Scans with Cards', 'scans_with_cards'),
                ('Scan Images', 'total_scan_images'),
                ('Scan Results', 'total_scan_results'),
                ('Cards from Scans', 'cards_from_scans')
            ]
            
            for metric_name, metric_key in metrics:
                dev_val = dev_stats[metric_key]
                prod_val = prod_stats[metric_key]
                match = "✅" if dev_val == prod_val else "❌"
                print(f"{metric_name:<25} {dev_val:<15} {prod_val:<15} {match:<10}")
        
        # Show recent scans
        print("\n📅 RECENT SCANS COMPARISON")
        print("-" * 40)
        
        if dev_stats and prod_stats:
            print("\n🔧 Development Recent Scans:")
            for scan in dev_stats['recent_scans']:
                scan_id, status, cards_found, images, created_at = scan
                print(f"  ID: {scan_id}, Status: {status}, Cards: {cards_found}, Images: {images}, Created: {created_at}")
            
            print("\n🌐 Production Recent Scans:")
            for scan in prod_stats['recent_scans']:
                scan_id, status, cards_found, images, created_at = scan
                print(f"  ID: {scan_id}, Status: {status}, Cards: {cards_found}, Images: {images}, Created: {created_at}")
        
        # Check table schemas
        print("\n🏗️  TABLE SCHEMA COMPARISON")
        print("-" * 40)
        
        dev_schemas = get_table_schemas(dev_conn, "Development")
        prod_schemas = get_table_schemas(prod_conn, "Production")
        
        if dev_schemas and prod_schemas:
            for table in ['scans', 'scan_images', 'scan_results']:
                if table in dev_schemas and table in prod_schemas:
                    dev_cols = set(col[0] for col in dev_schemas[table])
                    prod_cols = set(col[0] for col in prod_schemas[table])
                    
                    if dev_cols == prod_cols:
                        print(f"✅ {table} table: Schema matches")
                    else:
                        print(f"❌ {table} table: Schema differs")
                        dev_only = dev_cols - prod_cols
                        prod_only = prod_cols - dev_cols
                        if dev_only:
                            print(f"   Development only: {dev_only}")
                        if prod_only:
                            print(f"   Production only: {prod_only}")
                else:
                    print(f"❌ {table} table: Missing in one database")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
    
    finally:
        # Close connections
        if dev_conn:
            dev_conn.close()
        if prod_conn:
            prod_conn.close()

if __name__ == "__main__":
    compare_scan_data() 