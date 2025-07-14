#!/usr/bin/env python3
"""
Restore card data from JSON backup to the current database.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def get_database_connection():
    """Get database connection - works with both SQLite (local) and PostgreSQL (Railway)."""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Railway/Cloud environment with PostgreSQL
        import psycopg2
        from sqlalchemy import create_engine
        
        # Use SQLAlchemy for PostgreSQL connection
        engine = create_engine(database_url)
        return engine
    else:
        # Local environment with SQLite
        env_mode = os.getenv("ENV_MODE", "production")
        if env_mode == "development":
            db_path = Path(__file__).parent / "magic_cards_dev.db"
        else:
            db_path = Path(__file__).parent / "magic_cards.db"
        import sqlite3
        return sqlite3.connect(str(db_path))

def restore_from_backup(backup_file):
    """Restore cards from JSON backup file."""
    try:
        # Load backup data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        print(f"📦 Loading backup from: {backup_file}")
        print(f"📅 Backup timestamp: {backup_data.get('export_timestamp', 'Unknown')}")
        print(f"📊 Cards in backup: {len(backup_data.get('cards', []))}")
        
        # Get database connection
        conn = get_database_connection()
        
        # Handle different connection types
        if hasattr(conn, 'connect'):
            # SQLAlchemy engine
            engine = conn
            with engine.connect() as connection:
                return _restore_cards_to_connection(connection, backup_data, is_sqlalchemy=True)
        else:
            # Direct connection (SQLite)
            return _restore_cards_to_connection(conn, backup_data, is_sqlalchemy=False)
        
    except Exception as e:
        print(f"❌ Error restoring backup: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def _restore_cards_to_connection(connection, backup_data, is_sqlalchemy=False):
    """Restore cards to the given database connection."""
    try:
        # Clear existing cards (but keep scans)
        print("🗑️  Clearing existing cards...")
        if is_sqlalchemy:
            from sqlalchemy import text
            connection.execute(text("DELETE FROM cards"))
        else:
            connection.execute("DELETE FROM cards")
        
        # Insert cards from backup
        cards = backup_data.get('cards', [])
        print(f"📥 Restoring {len(cards)} cards...")
        
        for i, card in enumerate(cards):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(cards)} cards processed")
            
            if is_sqlalchemy:
                from sqlalchemy import text
                insert_sql = text("""
                    INSERT INTO cards (
                        name, set_code, set_name, collector_number, rarity, mana_cost,
                        type_line, oracle_text, flavor_text, power, toughness, colors,
                        image_url, price_usd, price_eur, price_tix, count, first_seen,
                        last_seen, notes, condition, is_example, duplicate_group,
                        stack_count, stack_id, unique_id, deleted, deleted_at, scan_id,
                        scan_result_id, import_status, added_method
                    ) VALUES (
                        :name, :set_code, :set_name, :collector_number, :rarity, :mana_cost,
                        :type_line, :oracle_text, :flavor_text, :power, :toughness, :colors,
                        :image_url, :price_usd, :price_eur, :price_tix, :count, :first_seen,
                        :last_seen, :notes, :condition, :is_example, :duplicate_group,
                        :stack_count, :stack_id, :unique_id, :deleted, :deleted_at, :scan_id,
                        :scan_result_id, :import_status, :added_method
                    )
                """)
                values = {
                    'name': card.get('name'),
                    'set_code': card.get('set_code'),
                    'set_name': card.get('set_name'),
                    'collector_number': card.get('collector_number'),
                    'rarity': card.get('rarity'),
                    'mana_cost': card.get('mana_cost'),
                    'type_line': card.get('type_line'),
                    'oracle_text': card.get('oracle_text'),
                    'flavor_text': card.get('flavor_text'),
                    'power': card.get('power'),
                    'toughness': card.get('toughness'),
                    'colors': card.get('colors'),
                    'image_url': card.get('image_url'),
                    'price_usd': card.get('price_usd'),
                    'price_eur': card.get('price_eur'),
                    'price_tix': card.get('price_tix'),
                    'count': card.get('count', 1),
                    'first_seen': card.get('first_seen'),
                    'last_seen': card.get('last_seen'),
                    'notes': card.get('notes'),
                    'condition': card.get('condition'),
                    'is_example': bool(card.get('is_example', 0)),
                    'duplicate_group': card.get('duplicate_group'),
                    'stack_count': card.get('stack_count'),
                    'stack_id': card.get('stack_id'),
                    'unique_id': card.get('unique_id'),
                    'deleted': bool(card.get('deleted', 0)),
                    'deleted_at': card.get('deleted_at'),
                    'scan_id': card.get('scan_id'),
                    'scan_result_id': card.get('scan_result_id'),
                    'import_status': card.get('import_status'),
                    'added_method': card.get('added_method')
                }
                connection.execute(insert_sql, values)
            else:
                insert_sql = """
                    INSERT INTO cards (
                        name, set_code, set_name, collector_number, rarity, mana_cost,
                        type_line, oracle_text, flavor_text, power, toughness, colors,
                        image_url, price_usd, price_eur, price_tix, count, first_seen,
                        last_seen, notes, condition, is_example, duplicate_group,
                        stack_count, stack_id, unique_id, deleted, deleted_at, scan_id,
                        scan_result_id, import_status, added_method
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """
                values = (
                    card.get('name'),
                    card.get('set_code'),
                    card.get('set_name'),
                    card.get('collector_number'),
                    card.get('rarity'),
                    card.get('mana_cost'),
                    card.get('type_line'),
                    card.get('oracle_text'),
                    card.get('flavor_text'),
                    card.get('power'),
                    card.get('toughness'),
                    card.get('colors'),
                    card.get('image_url'),
                    card.get('price_usd'),
                    card.get('price_eur'),
                    card.get('price_tix'),
                    card.get('count', 1),
                    card.get('first_seen'),
                    card.get('last_seen'),
                    card.get('notes'),
                    card.get('condition'),
                    card.get('is_example', 0),
                    card.get('duplicate_group'),
                    card.get('stack_count'),
                    card.get('stack_id'),
                    card.get('unique_id'),
                    card.get('deleted', 0),
                    card.get('deleted_at'),
                    card.get('scan_id'),
                    card.get('scan_result_id'),
                    card.get('import_status'),
                    card.get('added_method')
                )
                connection.execute(insert_sql, values)
        
        # Commit the transaction
        if is_sqlalchemy:
            connection.commit()
        else:
            connection.commit()
        
        print(f"✅ Successfully restored {len(cards)} cards to database!")
        return {
            "success": True,
            "cards_restored": len(cards),
            "backup_file": backup_data.get('export_timestamp', 'Unknown')
        }
        
    except Exception as e:
        print(f"❌ Error during restore: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python restore_from_backup.py <backup_file>")
        print("Example: python restore_from_backup.py backups/cards_export_20250713_055019.json")
        return
    
    backup_file = sys.argv[1]
    
    if not Path(backup_file).exists():
        print(f"❌ Backup file not found: {backup_file}")
        return
    
    result = restore_from_backup(backup_file)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 