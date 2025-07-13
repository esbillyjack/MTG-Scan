# Development Workflow

## Branching Strategy

This project uses a **Git Flow** inspired branching strategy to manage development and production releases.

### Branch Structure

#### 🚀 **`production`** 
- **Purpose**: Stable, production-ready code
- **Deployment**: This branch represents what's currently deployed/released
- **Updates**: Only receives merges from `main` after thorough testing
- **Protection**: Should be protected - no direct commits

#### 🔄 **`main`**
- **Purpose**: Integration branch for completed features
- **Status**: Stable, tested features ready for production
- **Updates**: Receives merges from `develop` and feature branches
- **Testing**: All features should be tested before merging here

#### 🛠️ **`develop`**
- **Purpose**: Active development branch
- **Status**: Latest development changes, may be unstable
- **Updates**: Receives merges from feature branches
- **Testing**: Features tested individually, integration testing ongoing

#### 🌟 **`feature/*`**
- **Purpose**: Individual feature development
- **Naming**: `feature/feature-name` (e.g., `feature/card-editing`, `feature/bulk-import`)
- **Lifecycle**: Created from `develop`, merged back to `develop`
- **Scope**: One feature per branch

## Workflow Process

### 1. Starting New Feature Development
```bash
# Switch to develop and pull latest
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on feature...
# Commit changes...

# Push feature branch
git push origin feature/your-feature-name
```

### 2. Completing a Feature
```bash
# Create pull request: feature/your-feature-name → develop
# After review and testing, merge to develop
git checkout develop
git merge feature/your-feature-name
git push origin develop

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### 3. Preparing for Production Release
```bash
# When develop is stable and ready for production
git checkout main
git merge develop
git push origin main

# Test thoroughly in main branch
# If all tests pass, merge to production
git checkout production
git merge main
git push origin production
```

### 4. Hotfixes (Emergency Production Fixes)
```bash
# Create hotfix branch from production
git checkout production
git checkout -b hotfix/critical-fix

# Make fix...
# Test thoroughly...

# Merge to production
git checkout production
git merge hotfix/critical-fix
git push origin production

# Also merge to main and develop
git checkout main
git merge hotfix/critical-fix
git push origin main

git checkout develop
git merge hotfix/critical-fix
git push origin develop
```

## Current Status

### Branch Overview
- **`production`**: v1.0 - Export functionality fixes (Commit: 853e31c)
- **`main`**: v1.0 - Same as production, ready for next release
- **`develop`**: v1.1-dev - Active development branch

### Recent Production Features
- ✅ Comprehensive sorting functionality
- ✅ Enhanced backup system with automation
- ✅ Fixed export functionality (CSV/Excel)
- ✅ Improved browse button with native file dialogs
- ✅ HTML features showcase

### Next Development Priorities
- [ ] Feature branches for new functionality
- [ ] Enhanced card editing capabilities
- [ ] Bulk import improvements
- [ ] Advanced search and filtering
- [ ] Performance optimizations

## Best Practices

### Commit Messages
- Use clear, descriptive commit messages
- Include feature scope: `feat: add bulk import functionality`
- Include fixes: `fix: resolve export file size issue`
- Include docs: `docs: update API documentation`

### Pull Requests
- Always create PR for merges to `main` or `production`
- Include description of changes
- Reference any related issues
- Ensure all tests pass

### Testing
- Test features in `develop` branch
- Thoroughly test `main` before production
- Never deploy untested code to `production`

## Emergency Procedures

### Rolling Back Production
```bash
# If production has issues, rollback to previous commit
git checkout production
git reset --hard <previous-good-commit>
git push origin production --force-with-lease
```

### Quick Status Check
```bash
# Check all branches
git branch -a

# Check current branch status
git status

# Check recent commits
git log --oneline -10
```

---

**Remember**: `production` is sacred - it should always represent working, deployable code! 🚀 