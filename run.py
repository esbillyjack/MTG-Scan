#!/usr/bin/env python3
"""
Run script for Magic Card Scanner
Starts the FastAPI server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_venv():
    """Check if virtual environment is activated"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def activate_venv():
    """Activate virtual environment if not already activated"""
    if check_venv():
        print("Virtual environment is already activated.")
        return True
    
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Virtual environment not found. Please run setup.py first.")
        return False
    
    # Try to activate virtual environment
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"
    
    if not python_exe.exists():
        print("Python executable not found in virtual environment.")
        return False
    
    # Use the virtual environment's Python
    os.environ['VIRTUAL_ENV'] = str(venv_path)
    os.environ['PATH'] = f"{venv_path}/bin:{os.environ.get('PATH', '')}"
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import openai
        import sqlalchemy
        import requests
        import pillow
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run setup.py to install dependencies.")
        return False

def check_env_file():
    """Check if .env file exists and has API key"""
    env_path = Path(".env")
    if not env_path.exists():
        print("Warning: .env file not found.")
        print("Please create .env file with your OpenAI API key.")
        return False
    
    with open(env_path, "r") as f:
        content = f.read()
        if "your_openai_api_key_here" in content:
            print("Warning: Please update .env file with your actual OpenAI API key.")
            return False
    
    return True

def main():
    """Main run function"""
    print("Starting Magic Card Scanner...")
    print("=" * 40)
    
    # Check virtual environment
    if not activate_venv():
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check environment file
    check_env_file()
    
    # Start the server
    print("Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        # Import and run the app
        sys.path.append(str(Path("backend")))
        from app import app
        import uvicorn
        
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 