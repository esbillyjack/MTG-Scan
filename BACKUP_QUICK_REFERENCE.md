# Database Backup Quick Reference

## 🚨 Emergency Recovery (If Database is Lost)

### Step 1: Stop the Application
```bash
# Stop the server immediately
pkill -f "python backend/app.py"
```

### Step 2: Check for Backups
```bash
python backup_manager.py list
```

### Step 3: Restore from Backup
```bash
# Use the most recent backup
python backup_manager.py restore --backup-file backups/backup_YYYYMMDD_HHMMSS.zip
```

### Step 4: Verify Restoration
```bash
python backup_manager.py stats
```

## 🔧 Regular Maintenance

### Create Manual Backup
```bash
python backup_manager.py backup --name "manual_backup_$(date +%Y%m%d_%H%M%S)"
```

### Start Automatic Backups
```bash
# Run in background (every 6 hours)
python auto_backup.py --daemon
```

### Check Backup Status
```bash
python backup_manager.py stats
```

## 📊 Database Information

### Current Stats
- **Total Cards**: 14
- **Total Scans**: 145  
- **Database Size**: 929KB
- **Upload Files**: 136

### Backup Location
- **Backup Directory**: `backups/`
- **Backup Format**: ZIP files with metadata
- **Retention**: Last 10 backups kept automatically

## 🛡️ Prevention Checklist

### Daily
- [ ] Check backup logs: `tail -f backup_scheduler.log`
- [ ] Verify disk space for backups

### Weekly  
- [ ] Test restore procedure
- [ ] Copy backups to external storage
- [ ] Review backup statistics

### Monthly
- [ ] Full backup integrity check
- [ ] Update backup documentation
- [ ] Test emergency recovery procedures

## 📞 Emergency Contacts

### If You Need Help:
1. **Document the problem** with timestamps
2. **Do not create new data** until recovery is complete
3. **Follow the emergency recovery steps** above
4. **Contact support** with backup logs and error messages

### Critical Files to Protect:
- `magic_cards.db` - Main database
- `uploads/` - Scan images
- `backups/` - Backup files

## ⚡ Quick Commands

```bash
# Force immediate backup
python auto_backup.py --force

# Export data for reconstruction
python backup_manager.py export

# Check if backups are working
python backup_manager.py stats

# List all available backups
python backup_manager.py list
```

## 🔍 Troubleshooting

### Backup Fails
```bash
# Check disk space
df -h

# Check backup directory permissions
ls -la backups/

# Check application logs
tail -f backup_scheduler.log
```

### Restore Fails
```bash
# Verify backup file integrity
python backup_manager.py list

# Try partial restore (database only)
python backup_manager.py restore --backup-file backup.zip --restore-uploads false
```

### Database Corrupted
```bash
# Export current data (if possible)
python backup_manager.py export

# Reconstruct from JSON
python backup_manager.py reconstruct --json-file backups/cards_export_YYYYMMDD_HHMMSS.json
```

## 📋 Recovery Time Estimates

| Scenario | Time Estimate |
|----------|---------------|
| Full backup restore | 1-5 minutes |
| JSON reconstruction | 2-10 minutes |
| Manual data entry | Hours to days |

## 🎯 Best Practices

1. **Always backup before major changes**
2. **Test restore procedures regularly**
3. **Keep backups in multiple locations**
4. **Monitor backup logs for errors**
5. **Document any custom procedures**

---

**Remember**: The best backup is the one you actually use. Set up automatic backups and test your recovery procedures regularly! 