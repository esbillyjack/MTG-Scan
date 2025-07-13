# Development & Production Workflow

## Overview

This document explains the proper development and production workflow for the Magic Card Scanner project. The setup ensures that development and production environments are completely isolated, preventing development changes from affecting the live production server.

## Directory Structure

```
projects/
├── magic-card-scanner/           # Development workspace (develop branch)
│   ├── backend/
│   ├── frontend/
│   ├── start_server_dev.sh      # Development server (port 8001)
│   ├── stop_server_dev.sh       # Stop development server
│   ├── deploy.sh                # Deployment script
│   └── check_servers.sh         # Check both servers
└── magic-card-scanner-production/ # Production deployment (production branch)
    ├── backend/
    ├── frontend/
    ├── start_server.sh          # Production server (port 8000)
    └── stop_server.sh           # Stop production server
```

## Branch Strategy

- **develop**: Active development branch (default working branch)
- **main**: Stable branch for staging/testing
- **production**: Live production branch

## Development Workflow

### 1. Daily Development

1. **Work in the development directory** (`magic-card-scanner/`)
2. **Always stay on the develop branch**
3. **Use the development server** for testing:
   ```bash
   ./start_server_dev.sh    # Starts on port 8001
   ./stop_server_dev.sh     # Stops development server
   ```

### 2. Testing Changes

- Development server runs on **port 8001**
- Uses development database (`magic_cards_dev.db`)
- Hot reloading enabled for faster development
- Environment variable: `ENV_MODE=development`

### 3. Committing Changes

```bash
git add .
git commit -m "Your commit message"
git push origin develop
```

## Production Deployment

### 1. Deployment Process

Use the automated deployment script:
```bash
./deploy.sh
```

This script will:
1. **Verify** you're on the develop branch
2. **Check** working directory is clean
3. **Run tests** (if available)
4. **Merge** develop → main → production
5. **Update** production directory
6. **Restart** production server
7. **Switch back** to develop branch

### 2. Deployment Options

```bash
./deploy.sh --help              # Show all options
./deploy.sh --skip-tests        # Skip test execution
./deploy.sh --force             # Force deploy from any branch
./deploy.sh --no-restart        # Don't restart production server
```

### 3. Manual Production Control

```bash
# In development directory (magic-card-scanner/)
./start_server.sh      # Start production server (port 8000)
./stop_server.sh       # Stop production server
```

## Server Management

### Check Server Status

```bash
./check_servers.sh
```

This shows:
- Development server status (port 8001)
- Production server status (port 8000)
- Health check results
- Recent log entries
- Quick action commands

### Server URLs

- **Development**: http://localhost:8001
- **Production**: http://localhost:8000

### Log Files

- **Development**: `logs/server_dev.log`
- **Production**: `../magic-card-scanner-production/logs/server.log`

## Environment Differences

| Feature | Development | Production |
|---------|-------------|------------|
| Port | 8001 | 8000 |
| Database | `magic_cards_dev.db` | `magic_cards.db` |
| Debug Mode | Enabled | Disabled |
| Hot Reload | Enabled | Disabled |
| Environment | `ENV_MODE=development` | `ENV_MODE=production` |

## Common Commands

### Development
```bash
# Start development server
./start_server_dev.sh

# Stop development server
./stop_server_dev.sh

# Check both servers
./check_servers.sh
```

### Production
```bash
# Deploy to production
./deploy.sh

# Check production logs
tail -f ../magic-card-scanner-production/logs/server.log

# Emergency production restart
./stop_server.sh && ./start_server.sh
```

## Best Practices

### 1. Development
- Always work on the `develop` branch
- Use the development server for testing
- Commit frequently with clear messages
- Test thoroughly before deploying

### 2. Deployment
- Only deploy from the `develop` branch
- Ensure working directory is clean
- Test the deployment in production
- Monitor logs after deployment

### 3. Emergency Procedures
- Use `./check_servers.sh` to diagnose issues
- Production logs: `../magic-card-scanner-production/logs/server.log`
- Emergency stop: `./stop_server.sh` (for production)
- Roll back: Deploy previous version from git

## Troubleshooting

### Development Server Won't Start
1. Check if port 8001 is in use: `lsof -ti:8001`
2. Verify virtual environment: `source venv/bin/activate`
3. Check logs: `tail -f logs/server_dev.log`

### Production Server Issues
1. Check production directory exists: `ls -la ../magic-card-scanner-production/`
2. Verify production branch: `cd ../magic-card-scanner-production && git branch`
3. Check production logs: `tail -f ../magic-card-scanner-production/logs/server.log`

### Deployment Failures
1. Ensure clean working directory: `git status`
2. Check you're on develop branch: `git branch`
3. Verify remote repositories: `git remote -v`
4. Use `./deploy.sh --force` if needed (caution!)

## Files and Scripts

| Script | Purpose |
|--------|---------|
| `start_server_dev.sh` | Start development server (port 8001) |
| `stop_server_dev.sh` | Stop development server |
| `start_server.sh` | Start production server (port 8000) |
| `stop_server.sh` | Stop production server |
| `deploy.sh` | Deploy from develop to production |
| `check_servers.sh` | Check status of both servers |

This workflow ensures complete isolation between development and production environments while maintaining an efficient deployment process. 