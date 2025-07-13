#!/usr/bin/env python3
"""
Database Backup Manager for Magic Card Scanner

This script provides comprehensive backup and recovery capabilities for the Magic Card Scanner database.
It handles full backups (database + uploads), restoration, integrity checks, and data export/reconstruction.

Features:
- Full backup with database and upload files
- Automatic backup rotation (keeps last 10)
- Integrity verification
- Data export to JSON for reconstruction
- Emergency recovery procedures
- Local backup storage (not committed to git)

Usage:
    python backup_manager.py backup [--name backup_name]
    python backup_manager.py restore --backup-file backup.zip
    python backup_manager.py list
    python backup_manager.py stats
    python backup_manager.py export
    python backup_manager.py reconstruct --json-file export.json
"""

import os
import shutil
import sqlite3
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import List, Dict, Optional, Tuple
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, db_path: str = "magic_cards.db", uploads_path: str = "uploads"):
        self.db_path = db_path
        self.uploads_path = uploads_path
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup retention settings
        self.max_backups = 10  # Keep last 10 backups
        self.auto_backup_interval = timedelta(hours=6)  # Auto backup every 6 hours
        
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a comprehensive backup including database and uploads.
        Returns the backup filename.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        logger.info(f"Creating backup: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup database
                if os.path.exists(self.db_path):
                    zipf.write(self.db_path, "database/magic_cards.db")
                    logger.info(f"Database backed up: {self.db_path}")
                
                # Backup uploads directory
                if os.path.exists(self.uploads_path):
                    for root, dirs, files in os.walk(self.uploads_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.uploads_path)
                            zipf.write(file_path, f"uploads/{arcname}")
                    logger.info(f"Uploads backed up: {self.uploads_path}")
                
                # Create backup metadata
                metadata = {
                    "backup_timestamp": timestamp,
                    "backup_name": backup_name,
                    "database_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                    "uploads_count": len([f for f in Path(self.uploads_path).rglob("*") if f.is_file()]) if os.path.exists(self.uploads_path) else 0,
                    "version": "1.0.0"
                }
                
                zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
                
            logger.info(f"Backup completed successfully: {backup_path}")
            self._cleanup_old_backups()
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def restore_backup(self, backup_path: str, restore_db: bool = True, restore_uploads: bool = True) -> bool:
        """
        Restore from a backup file.
        Returns True if successful.
        """
        logger.info(f"Restoring from backup: {backup_path}")
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Verify backup integrity
                if not self._verify_backup_integrity(zipf):
                    logger.error("Backup integrity check failed")
                    return False
                
                # Restore database
                if restore_db and "database/magic_cards.db" in zipf.namelist():
                    # Create backup of current database before restoring
                    current_backup = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    if os.path.exists(self.db_path):
                        shutil.copy2(self.db_path, current_backup)
                        logger.info(f"Current database backed up as: {current_backup}")
                    
                    # Extract and restore database
                    zipf.extract("database/magic_cards.db", "temp_restore")
                    shutil.move("temp_restore/database/magic_cards.db", self.db_path)
                    shutil.rmtree("temp_restore")
                    logger.info("Database restored successfully")
                
                # Restore uploads
                if restore_uploads:
                    uploads_in_backup = [f for f in zipf.namelist() if f.startswith("uploads/")]
                    if uploads_in_backup:
                        # Backup current uploads
                        current_uploads_backup = f"pre_restore_uploads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        if os.path.exists(self.uploads_path):
                            shutil.copytree(self.uploads_path, current_uploads_backup)
                            logger.info(f"Current uploads backed up as: {current_uploads_backup}")
                        
                        # Extract uploads
                        zipf.extractall("temp_restore")
                        if os.path.exists(self.uploads_path):
                            shutil.rmtree(self.uploads_path)
                        shutil.move("temp_restore/uploads", self.uploads_path)
                        shutil.rmtree("temp_restore")
                        logger.info("Uploads restored successfully")
                
                # Read and log metadata
                if "backup_metadata.json" in zipf.namelist():
                    metadata = json.loads(zipf.read("backup_metadata.json"))
                    logger.info(f"Restored backup from: {metadata.get('backup_timestamp', 'Unknown')}")
                
            logger.info("Backup restoration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def _verify_backup_integrity(self, zipf: zipfile.ZipFile) -> bool:
        """Verify backup file integrity."""
        try:
            # Check for required files
            required_files = ["backup_metadata.json"]
            for file in required_files:
                if file not in zipf.namelist():
                    logger.error(f"Missing required file in backup: {file}")
                    return False
            
            # Test zip file integrity
            zipf.testzip()
            return True
            
        except Exception as e:
            logger.error(f"Backup integrity check failed: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backups to maintain retention policy."""
        backup_files = sorted(
            [f for f in self.backup_dir.glob("*.zip")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if len(backup_files) > self.max_backups:
            for old_backup in backup_files[self.max_backups:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
    
    def list_backups(self) -> List[Dict]:
        """List all available backups with metadata."""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if "backup_metadata.json" in zipf.namelist():
                        metadata = json.loads(zipf.read("backup_metadata.json"))
                        backups.append({
                            "filename": backup_file.name,
                            "path": str(backup_file),
                            "size": backup_file.stat().st_size,
                            "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                            "metadata": metadata
                        })
                    else:
                        # Legacy backup without metadata
                        backups.append({
                            "filename": backup_file.name,
                            "path": str(backup_file),
                            "size": backup_file.stat().st_size,
                            "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                            "metadata": {"backup_timestamp": "Unknown", "version": "Legacy"}
                        })
            except Exception as e:
                logger.error(f"Error reading backup {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def export_database_schema(self) -> str:
        """Export database schema for reconstruction purposes."""
        schema_path = self.backup_dir / f"schema_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        try:
            conn = sqlite3.connect(self.db_path)
            with open(schema_path, 'w') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            conn.close()
            
            logger.info(f"Database schema exported to: {schema_path}")
            return str(schema_path)
            
        except Exception as e:
            logger.error(f"Schema export failed: {e}")
            raise
    
    def export_card_data_json(self) -> str:
        """Export card data as JSON for reconstruction."""
        json_path = self.backup_dir / f"cards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all cards
            cards = conn.execute("SELECT * FROM cards WHERE deleted = 0").fetchall()
            
            # Convert to JSON-serializable format
            cards_data = []
            for card in cards:
                card_dict = dict(card)
                # Convert datetime objects to strings
                for key, value in card_dict.items():
                    if isinstance(value, datetime):
                        card_dict[key] = value.isoformat()
                cards_data.append(card_dict)
            
            # Get scan data
            scans = conn.execute("SELECT * FROM scans").fetchall()
            scans_data = [dict(scan) for scan in scans]
            
            # Get scan results
            scan_results = conn.execute("SELECT * FROM scan_results").fetchall()
            scan_results_data = [dict(result) for result in scan_results]
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "cards": cards_data,
                "scans": scans_data,
                "scan_results": scan_results_data
            }
            
            with open(json_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            conn.close()
            logger.info(f"Card data exported to: {json_path}")
            return str(json_path)
            
        except Exception as e:
            logger.error(f"Card data export failed: {e}")
            raise
    
    def reconstruct_from_json(self, json_file: str) -> bool:
        """Reconstruct database from JSON export."""
        logger.info(f"Reconstructing database from: {json_file}")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Create new database
            from backend.database import init_db, SessionLocal, Card, Scan, ScanResult
            
            # Initialize database
            init_db()
            db = SessionLocal()
            
            try:
                # Clear existing data
                db.query(Card).delete()
                db.query(Scan).delete()
                db.query(ScanResult).delete()
                db.commit()
                
                # Import scans
                for scan_data in data.get("scans", []):
                    scan = Scan(**scan_data)
                    db.add(scan)
                db.commit()
                
                # Import scan results
                for result_data in data.get("scan_results", []):
                    result = ScanResult(**result_data)
                    db.add(result)
                db.commit()
                
                # Import cards
                for card_data in data.get("cards", []):
                    card = Card(**card_data)
                    db.add(card)
                db.commit()
                
                logger.info("Database reconstruction completed successfully")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database reconstruction failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get current database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            stats = {
                "total_cards": conn.execute("SELECT COUNT(*) FROM cards WHERE deleted = 0").fetchone()[0],
                "total_scans": conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0],
                "total_scan_results": conn.execute("SELECT COUNT(*) FROM scan_results").fetchone()[0],
                "database_size": os.path.getsize(self.db_path),
                "uploads_count": len([f for f in Path(self.uploads_path).rglob("*") if f.is_file()]) if os.path.exists(self.uploads_path) else 0,
                "last_backup": None
            }
            
            # Get last backup info
            backups = self.list_backups()
            if backups:
                stats["last_backup"] = backups[0]["created"]
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


def main():
    """Command line interface for backup manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Magic Card Scanner Backup Manager")
    parser.add_argument("action", choices=["backup", "restore", "list", "export", "reconstruct", "stats"])
    parser.add_argument("--backup-file", help="Backup file for restore/reconstruct")
    parser.add_argument("--json-file", help="JSON file for reconstruction")
    parser.add_argument("--name", help="Custom backup name")
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.action == "backup":
        backup_path = manager.create_backup(args.name)
        print(f"Backup created: {backup_path}")
    
    elif args.action == "restore":
        if not args.backup_file:
            print("Error: --backup-file required for restore")
            return
        success = manager.restore_backup(args.backup_file)
        print(f"Restore {'successful' if success else 'failed'}")
    
    elif args.action == "list":
        backups = manager.list_backups()
        print(f"Found {len(backups)} backups:")
        for backup in backups:
            print(f"  {backup['filename']} ({backup['size']} bytes) - {backup['created']}")
    
    elif args.action == "export":
        schema_path = manager.export_database_schema()
        json_path = manager.export_card_data_json()
        print(f"Schema exported: {schema_path}")
        print(f"Card data exported: {json_path}")
    
    elif args.action == "reconstruct":
        if not args.json_file:
            print("Error: --json-file required for reconstruction")
            return
        success = manager.reconstruct_from_json(args.json_file)
        print(f"Reconstruction {'successful' if success else 'failed'}")
    
    elif args.action == "stats":
        stats = manager.get_database_stats()
        print("Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main() 