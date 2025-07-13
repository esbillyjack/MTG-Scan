# Database Safety and Backup System

## 🛡️ Overview

The Magic Card Scanner includes a comprehensive backup and recovery system designed to protect your valuable card data against catastrophic loss. **All backups are stored locally only** and are not committed to version control to prevent large files from being pushed to the repository.

## 📁 Backup Storage

- **Location**: `backups/` directory (local only)
- **Format**: ZIP files containing database + upload files
- **Retention**: Automatic rotation keeps last 10 backups
- **Git Status**: Excluded from version control (see `.gitignore`)

## 🔧 Backup Components

### What Gets Backed Up
- **Database**: `magic_cards.db` (SQLite)
- **Upload Files**: `uploads/` directory (scan images)
- **Metadata**: Backup timestamp, file counts, sizes

### What's NOT Backed Up
- Virtual environment (`venv/`)
- Python cache files (`__pycache__/`)
- IDE files (`.vscode/`, `.idea/`)
- Log files

## 🚀 Quick Start

### Create Your First Backup
```bash
python backup_manager.py backup
```

### Check Available Backups
```bash
python backup_manager.py list
```

### View Backup Statistics
```bash
python backup_manager.py stats
```

## 🔄 Automatic Backups

### Start Automatic Backup Scheduler
```bash
python auto_backup.py --daemon
```

This will:
- Create backups every 6 hours
- Keep only the last 10 backups
- Log all activities to `backup_scheduler.log`

### Stop Automatic Backups
```bash
pkill -f "auto_backup.py"
```

## 🚨 Emergency Recovery

### If Database is Lost or Corrupted

1. **Stop the application immediately**
   ```bash
   pkill -f "python backend/app.py"
   ```

2. **List available backups**
   ```bash
   python backup_manager.py list
   ```

3. **Restore from backup**
   ```bash
   python backup_manager.py restore --backup-file backups/backup_YYYYMMDD_HHMMSS.zip
   ```

4. **Verify restoration**
   ```bash
   python backup_manager.py stats
   ```

5. **Restart the application**
   ```bash
   python backend/app.py
   ```

## 📊 Backup Management

### Manual Backup Operations

```bash
# Create backup with custom name
python backup_manager.py backup --name "before_major_changes"

# List all backups
python backup_manager.py list

# Check backup integrity
python backup_manager.py verify --backup-file backup.zip

# Export data to JSON (for reconstruction)
python backup_manager.py export

# Reconstruct database from JSON
python backup_manager.py reconstruct --json-file export.json
```

### Backup Rotation

The system automatically:
- Keeps the last 10 backups
- Removes older backups to save space
- Logs rotation activities

## 🔍 Monitoring and Maintenance

### Daily Checks
- [ ] Verify backup scheduler is running: `ps aux | grep auto_backup`
- [ ] Check backup logs: `tail -f backup_scheduler.log`
- [ ] Ensure sufficient disk space: `df -h`

### Weekly Checks
- [ ] Test restore procedure on test environment
- [ ] Copy backups to external storage (USB drive, cloud)
- [ ] Review backup statistics: `python backup_manager.py stats`

### Monthly Checks
- [ ] Full backup integrity verification
- [ ] Update backup documentation
- [ ] Test emergency recovery procedures

## 📋 Backup Statistics

### Current Database Stats
- **Total Cards**: 14
- **Total Scans**: 145
- **Database Size**: 929KB
- **Upload Files**: 136
- **Total Data Size**: ~65MB

### Backup Performance
- **Backup Time**: 30-60 seconds
- **Backup Size**: ~65MB per backup
- **Storage Required**: ~650MB for 10 backups

## 🛠️ Troubleshooting

### Common Issues

**Backup Fails**
```bash
# Check disk space
df -h

# Check permissions
ls -la backups/

# Check application logs
tail -f backup_scheduler.log
```

**Restore Fails**
```bash
# Verify backup file integrity
python backup_manager.py list

# Try partial restore (database only)
python backup_manager.py restore --backup-file backup.zip --restore-uploads false
```

**Database Corrupted**
```bash
# Export current data (if possible)
python backup_manager.py export

# Reconstruct from JSON
python backup_manager.py reconstruct --json-file export.json
```

## 🔐 Security Considerations

### Local Storage Benefits
- **Privacy**: No cloud storage of your data
- **Control**: Complete control over backup files
- **Speed**: Fast local access and restoration
- **Cost**: No cloud storage fees

### Recommended Practices
1. **External Backup**: Copy `backups/` to external drive weekly
2. **Cloud Backup**: Consider cloud storage for critical backups
3. **Multiple Locations**: Keep backups in different physical locations
4. **Regular Testing**: Test restore procedures monthly

## 📞 Emergency Contacts

### If You Need Help
1. **Document the problem** with timestamps
2. **Do not create new data** until recovery is complete
3. **Follow emergency recovery steps** above
4. **Contact support** with backup logs and error messages

### Critical Files to Protect
- `magic_cards.db` - Main database
- `uploads/` - Scan images
- `backups/` - Backup files (local only)

## ⚡ Quick Reference

```bash
# Emergency recovery
pkill -f "python backend/app.py"
python backup_manager.py list
python backup_manager.py restore --backup-file backups/latest.zip
python backend/app.py

# Regular maintenance
python backup_manager.py backup
python auto_backup.py --daemon
python backup_manager.py stats
```

---

**Remember**: The best backup is the one you actually use. Set up automatic backups and test your recovery procedures regularly!

**Note**: All backups are stored locally in the `backups/` directory and are excluded from git to prevent large files from being committed to the repository. 