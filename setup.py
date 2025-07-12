#!/usr/bin/env python3
"""
Setup script for Magic Card Scanner
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def create_virtual_environment():
    """Create a virtual environment"""
    print("Creating virtual environment...")
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists.")
        return True
    
    try:
        venv.create("venv", with_pip=True)
        print("Virtual environment created successfully.")
        return True
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing dependencies...")
    
    # Determine the pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    result = run_command(f"{pip_cmd} install -r requirements.txt")
    if result:
        print("Dependencies installed successfully.")
        return True
    else:
        print("Failed to install dependencies.")
        return False

def create_env_file():
    """Create .env file template"""
    env_content = """# Magic Card Scanner Environment Variables
# Add your OpenAI API key here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Database configuration
DATABASE_URL=sqlite:///./magic_cards.db
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_content)
        print("Created .env file template.")
        print("Please add your OpenAI API key to the .env file.")
    else:
        print(".env file already exists.")

def create_directories():
    """Create necessary directories"""
    directories = ["uploads", "frontend"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("Created necessary directories.")

def main():
    """Main setup function"""
    print("Setting up Magic Card Scanner...")
    print("=" * 40)
    
    # Create directories
    create_directories()
    
    # Create virtual environment
    if not create_virtual_environment():
        print("Failed to create virtual environment.")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies.")
        return False
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 40)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Add your OpenAI API key to the .env file")
    print("2. Activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")
    print("3. Run the application:")
    print("   python backend/app.py")
    print("4. Open http://localhost:8000 in your browser")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 