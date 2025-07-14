#!/usr/bin/env python3
"""
Sync all data from SQLite development database to PostgreSQL Railway database
"""

import sqlite3
import os
from sqlalchemy import create_engine, text

def get_database_connections():
    """Get both SQLite and PostgreSQL connections"""
    
    # SQLite (source)
    sqlite_conn = sqlite3.connect('magic_cards_dev.db')
    
    # PostgreSQL (destination)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        return None, None
    
    pg_engine = create_engine(database_url)
    
    return sqlite_conn, pg_engine

def clear_postgres_tables(pg_engine):
    """Clear all relevant tables in PostgreSQL"""
    print("🗑️  Clearing PostgreSQL tables...")
    
    with pg_engine.connect() as conn:
        # Clear in reverse dependency order
        conn.execute(text("DELETE FROM cards"))
        conn.execute(text("DELETE FROM scan_results"))
        conn.execute(text("DELETE FROM scan_images"))
        conn.execute(text("DELETE FROM scans"))
        conn.commit()
    
    print("✅ PostgreSQL tables cleared")

def copy_table_data(sqlite_conn, pg_engine, table_name, columns):
    """Copy data from SQLite table to PostgreSQL table"""
    print(f"📥 Copying {table_name}...")
    
    # Get data from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   No data found in {table_name}")
        return 0
    
    print(f"   Found {len(rows)} rows in SQLite")
    
    # Copy to PostgreSQL
    with pg_engine.connect() as pg_conn:
        for i, row in enumerate(rows):
            if i % 50 == 0:
                print(f"   Progress: {i}/{len(rows)} rows")
            
            # Create placeholders for SQL
            placeholders = ', '.join([f':col{i}' for i in range(len(columns))])
            column_list = ', '.join(columns)
            
            insert_sql = text(f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})")
            
            # Create parameter dict
            params = {f'col{i}': value for i, value in enumerate(row)}
            
            # Special handling for cards table boolean fields
            if table_name == 'cards':
                # Find column indices for is_example and deleted
                if 'is_example' in columns:
                    idx = columns.index('is_example')
                    params[f'col{idx}'] = bool(params[f'col{idx}'])
                if 'deleted' in columns:
                    idx = columns.index('deleted')
                    params[f'col{idx}'] = bool(params[f'col{idx}'])
            
            pg_conn.execute(insert_sql, params)
        
        pg_conn.commit()
    
    print(f"✅ Copied {len(rows)} rows to {table_name}")
    return len(rows)

def sync_all_data():
    """Sync all data from SQLite to PostgreSQL"""
    print("🔄 Starting SQLite to PostgreSQL sync...")
    
    # Get connections
    sqlite_conn, pg_engine = get_database_connections()
    if not sqlite_conn or not pg_engine:
        return False
    
    try:
        # Clear PostgreSQL tables
        clear_postgres_tables(pg_engine)
        
        # Copy data in dependency order
        tables = [
            ('scans', ['id', 'created_at', 'updated_at', 'status', 'total_images', 'processed_images', 'total_cards_found', 'unknown_cards_count', 'notes']),
            ('scan_images', ['id', 'scan_id', 'filename', 'original_filename', 'file_path', 'processed_at', 'cards_found', 'processing_error']),
            ('scan_results', ['id', 'scan_id', 'scan_image_id', 'card_name', 'set_code', 'set_name', 'collector_number', 'confidence_score', 'status', 'user_notes', 'card_data', 'ai_raw_response', 'created_at', 'decided_at']),
            ('cards', ['id', 'unique_id', 'name', 'set_code', 'set_name', 'collector_number', 'rarity', 'mana_cost', 'type_line', 'oracle_text', 'flavor_text', 'power', 'toughness', 'colors', 'image_url', 'price_usd', 'price_eur', 'price_tix', 'count', 'stack_count', 'notes', 'condition', 'is_example', 'duplicate_group', 'stack_id', 'deleted', 'first_seen', 'last_seen', 'deleted_at', 'scan_id', 'scan_result_id', 'import_status', 'added_method'])
        ]
        
        total_rows = 0
        for table_name, columns in tables:
            rows_copied = copy_table_data(sqlite_conn, pg_engine, table_name, columns)
            total_rows += rows_copied
        
        print(f"🎉 Sync completed! Total rows copied: {total_rows}")
        return True
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        return False
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    success = sync_all_data()
    if success:
        print("✅ Database sync completed successfully!")
    else:
        print("❌ Database sync failed!") 