#!/bin/bash

# Magic Card Scanner Deployment Script
# Handles deployment from development to production

set -e  # Exit on any error

PRODUCTION_DIR="../magic-card-scanner-production"
CURRENT_BRANCH=$(git branch --show-current)

echo "🚀 Magic Card Scanner Deployment Script"
echo "======================================="
echo "Current branch: $CURRENT_BRANCH"

# Function to check if production server is running
check_production_server() {
    if [ -f "$PRODUCTION_DIR/logs/server.pid" ]; then
        PID=$(cat "$PRODUCTION_DIR/logs/server.pid")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Production server is running (PID: $PID)"
            return 0
        else
            echo "⚠️ Production server PID file exists but process is not running"
            rm -f "$PRODUCTION_DIR/logs/server.pid"
            return 1
        fi
    else
        echo "ℹ️ Production server is not running"
        return 1
    fi
}

# Function to stop production server
stop_production_server() {
    echo "🛑 Stopping production server..."
    if [ -f "$PRODUCTION_DIR/logs/server.pid" ]; then
        PID=$(cat "$PRODUCTION_DIR/logs/server.pid")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                echo "Force killing production server..."
                kill -9 $PID
            fi
            rm -f "$PRODUCTION_DIR/logs/server.pid"
            echo "✅ Production server stopped"
        else
            echo "⚠️ Production server process not found"
            rm -f "$PRODUCTION_DIR/logs/server.pid"
        fi
    else
        echo "ℹ️ No production server PID file found"
    fi
}

# Function to start production server
start_production_server() {
    echo "🚀 Starting production server..."
    cd "$PRODUCTION_DIR"
    ./start_server.sh
    cd - > /dev/null
    echo "✅ Production server started"
}

# Parse command line arguments
SKIP_TESTS=false
FORCE_DEPLOY=false
NO_RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-tests    Skip running tests before deployment"
            echo "  --force         Force deployment even if on wrong branch"
            echo "  --no-restart    Don't restart the production server"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if we're on the develop branch
if [ "$CURRENT_BRANCH" != "develop" ] && [ "$FORCE_DEPLOY" = false ]; then
    echo "❌ Error: You must be on the 'develop' branch to deploy"
    echo "Current branch: $CURRENT_BRANCH"
    echo "Use --force to override this check"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit your changes first."
    git status --short
    exit 1
fi

# Run tests if not skipping
if [ "$SKIP_TESTS" = false ]; then
    echo "🧪 Running tests..."
    if [ -f "test.py" ]; then
        python test.py
    elif [ -f "tests/test_main.py" ]; then
        python -m pytest tests/
    else
        echo "⚠️ No tests found, skipping..."
    fi
fi

# Merge develop to main
echo "🔄 Merging develop to main..."
git checkout main
git pull origin main
git merge develop --no-edit
git push origin main

# Merge main to production
echo "🔄 Merging main to production..."
git checkout production
git pull origin production  
git merge main --no-edit
git push origin production

# Update production directory
echo "📦 Updating production deployment..."
cd "$PRODUCTION_DIR"
git pull origin production

# Stop production server if running and restart is requested
if [ "$NO_RESTART" = false ]; then
    if check_production_server; then
        stop_production_server
    fi
    
    # Start production server
    start_production_server
fi

cd - > /dev/null

# Switch back to develop branch
echo "🔄 Switching back to develop branch..."
git checkout develop

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 Production server: http://localhost:8000"
echo "🛠️ Development server: http://localhost:8001"
echo ""
echo "Next steps:"
echo "- Test the production deployment"
echo "- Monitor logs: tail -f $PRODUCTION_DIR/logs/server.log"
echo "- Check status: ./check_servers.sh" 