#!/usr/bin/env python3
"""
Automatic Backup Scheduler for Magic Card Scanner
Runs in the background to perform regular backups.
"""

import time
import threading
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path
from backup_manager import BackupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoBackupScheduler:
    def __init__(self, backup_interval_hours: int = 6):
        self.backup_manager = BackupManager()
        self.backup_interval_hours = backup_interval_hours
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the automatic backup scheduler."""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        
        # Schedule backups
        schedule.every(self.backup_interval_hours).hours.do(self._perform_backup)
        
        # Also schedule a backup on startup if it's been more than 6 hours since last backup
        self._check_and_backup_if_needed()
        
        logger.info(f"Auto backup scheduler started (every {self.backup_interval_hours} hours)")
        
        # Run the scheduler in a separate thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the automatic backup scheduler."""
        self.running = False
        schedule.clear()
        logger.info("Auto backup scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _perform_backup(self):
        """Perform a scheduled backup."""
        try:
            logger.info("Performing scheduled backup...")
            backup_path = self.backup_manager.create_backup(f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            logger.info(f"Scheduled backup completed: {backup_path}")
            
            # Log backup statistics
            stats = self.backup_manager.get_database_stats()
            logger.info(f"Backup stats: {stats['total_cards']} cards, {stats['database_size']} bytes")
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def _check_and_backup_if_needed(self):
        """Check if we need an immediate backup based on last backup time."""
        try:
            backups = self.backup_manager.list_backups()
            if not backups:
                logger.info("No previous backups found, performing initial backup...")
                self._perform_backup()
                return
            
            last_backup = backups[0]["created"]
            time_since_last = datetime.now() - last_backup
            
            if time_since_last > timedelta(hours=self.backup_interval_hours):
                logger.info(f"Last backup was {time_since_last} ago, performing backup...")
                self._perform_backup()
            else:
                logger.info(f"Last backup was {time_since_last} ago, no backup needed yet")
                
        except Exception as e:
            logger.error(f"Error checking backup status: {e}")
    
    def force_backup(self):
        """Force an immediate backup."""
        logger.info("Forcing immediate backup...")
        self._perform_backup()


def main():
    """Command line interface for auto backup scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Magic Card Scanner Auto Backup Scheduler")
    parser.add_argument("--interval", type=int, default=6, help="Backup interval in hours (default: 6)")
    parser.add_argument("--force", action="store_true", help="Force an immediate backup")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (continuous)")
    
    args = parser.parse_args()
    
    scheduler = AutoBackupScheduler(args.interval)
    
    if args.force:
        scheduler.force_backup()
    elif args.daemon:
        print("Starting auto backup scheduler...")
        scheduler.start()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping auto backup scheduler...")
            scheduler.stop()
    else:
        print("Auto backup scheduler ready. Use --daemon to run continuously or --force for immediate backup.")


if __name__ == "__main__":
    main() 