#!/usr/bin/env python3
"""
Deployment Readiness Checker for Magic Card Scanner
Verifies that the application is ready for Railway deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_environment_variable(var_name, description, required=True):
    """Check if an environment variable is set"""
    value = os.getenv(var_name)
    if value:
        if var_name == "OPENAI_API_KEY":
            # Don't print the full API key
            print(f"✅ {description}: {var_name}=sk-...{value[-10:]}")
        else:
            print(f"✅ {description}: {var_name}={value}")
        return True
    else:
        if required:
            print(f"❌ {description}: {var_name} - NOT SET")
        else:
            print(f"⚠️ {description}: {var_name} - NOT SET (optional)")
        return not required

def check_python_dependencies():
    """Check if required Python packages are installed"""
    print("\n🔍 Checking Python dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2",
        "openai",
        "dotenv"
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_good = False
    
    return all_good

def check_database_connection():
    """Check if database connection works"""
    print("\n🗄️ Checking database connection...")
    
    try:
        from backend.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_git_status():
    """Check git status"""
    print("\n📝 Checking Git status...")
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("⚠️ You have uncommitted changes:")
            print(result.stdout)
            print("Consider committing changes before deployment.")
        else:
            print("✅ Git working directory is clean")
        
        # Check current branch
        result = subprocess.run(["git", "branch", "--show-current"], 
                              capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
        print(f"✅ Current branch: {branch}")
        
        return True
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository or git not available")
        return False

def main():
    """Main deployment readiness check"""
    print("🚀 Magic Card Scanner - Deployment Readiness Check")
    print("=" * 60)
    
    all_checks = True
    
    # Check required files
    print("\n📁 Checking required files...")
    checks = [
        check_file_exists("requirements.txt", "Requirements file"),
        check_file_exists("railway.toml", "Railway configuration"),
        check_file_exists("backend/app.py", "Main application file"),
        check_file_exists("backend/database.py", "Database configuration"),
        check_file_exists("migrate_to_postgresql.py", "Migration script"),
        check_file_exists("RAILWAY_DEPLOYMENT_GUIDE.md", "Deployment guide"),
    ]
    all_checks = all_checks and all(checks)
    
    # Check environment variables
    print("\n🔧 Checking environment variables...")
    env_checks = [
        check_environment_variable("OPENAI_API_KEY", "OpenAI API Key", required=True),
        check_environment_variable("JWT_SECRET_KEY", "JWT Secret Key", required=False),
        check_environment_variable("ENV_MODE", "Environment Mode", required=False),
    ]
    all_checks = all_checks and all(env_checks)
    
    # Check Python dependencies
    dep_check = check_python_dependencies()
    all_checks = all_checks and dep_check
    
    # Check database connection
    db_check = check_database_connection()
    all_checks = all_checks and db_check
    
    # Check git status
    git_check = check_git_status()
    # Git check is informational only, doesn't affect deployment readiness
    
    print("\n" + "=" * 60)
    
    if all_checks:
        print("🎉 DEPLOYMENT READY!")
        print("Your application is ready for Railway deployment.")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Follow the RAILWAY_DEPLOYMENT_GUIDE.md")
        print("3. Create Railway project and deploy")
        return True
    else:
        print("❌ NOT READY FOR DEPLOYMENT")
        print("Please fix the issues above before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 