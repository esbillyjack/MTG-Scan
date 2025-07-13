# Magic Card Scanner - Installation Guide

This guide will walk you through setting up the Magic Card Scanner on your system.

## 📋 Prerequisites

Before installing, ensure you have:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **OpenAI API Key** - [Get API Key](https://platform.openai.com/api-keys)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

## 🚀 Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/esbillyjack/MTG-Scan.git
cd MTG-Scan
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your OpenAI API key
# Use your preferred text editor:
nano .env
# or
vim .env
# or
code .env
```

Add your OpenAI API key to the `.env` file:
```
OPENAI_API_KEY=your_actual_api_key_here
```

### 5. Start the Server

```bash
# Make scripts executable (macOS/Linux)
chmod +x *.sh

# Start the server
./start_server.sh
```

### 6. Access the Application

Open your web browser and go to:
```
http://localhost:8000
```

## 🛠️ Detailed Installation

### System Requirements

#### Minimum Requirements
- **OS**: macOS 10.14+, Windows 10+, or Linux (Ubuntu 18.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space for installation, more for card database
- **Network**: Internet connection for AI processing and price lookup

#### Recommended Requirements
- **OS**: Latest version of macOS, Windows 11, or Ubuntu 20.04+
- **RAM**: 8GB or more
- **Storage**: 5GB+ free space
- **Network**: Stable broadband connection

### Python Setup

#### Installing Python

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
# https://www.python.org/downloads/
```

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Verify Installation
```bash
python --version  # Should show Python 3.8+
pip --version     # Should show pip version
```

### Virtual Environment Setup

Virtual environments isolate your project dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate (you'll need to do this each time you work on the project)
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Your prompt should now show (venv)
```

### Dependency Installation

```bash
# Ensure you're in the virtual environment
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### OpenAI API Key Setup

1. **Get API Key**:
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Sign up or log in
   - Create a new API key
   - Copy the key (keep it secure!)

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```

3. **Edit .env file**:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

### Database Setup

The application uses SQLite by default - no additional setup required!

The database file (`magic_cards.db`) will be created automatically when you first run the application.

### Server Configuration

#### Default Configuration
- **Port**: 8000
- **Host**: localhost
- **Database**: SQLite (magic_cards.db)
- **Logs**: logs/server.log

#### Custom Configuration
Edit `.env` file to customize:
```
PORT=8080
HOST=0.0.0.0
DATABASE_URL=sqlite:///./my_cards.db
```

## 🔧 Server Management

### Starting the Server

```bash
# Start server (recommended)
./start_server.sh

# Or start manually
python -m uvicorn backend.app:app --host localhost --port 8000
```

### Stopping the Server

```bash
# Stop server
./stop_server.sh

# Or manually find and kill process
ps aux | grep python
kill <process_id>
```

### Checking Server Status

```bash
# Check if server is running
./check_server.sh

# Or check manually
curl http://localhost:8000/health
```

### Viewing Logs

```bash
# View recent logs
tail -f logs/server.log

# View all logs
cat logs/server.log
```

## 🐛 Troubleshooting

### Common Issues

#### Python Not Found
**Error**: `python: command not found`
**Solution**: 
- Ensure Python is installed and in PATH
- Try `python3` instead of `python`
- On Windows, reinstall Python with "Add to PATH" checked

#### Permission Denied (macOS/Linux)
**Error**: `Permission denied: './start_server.sh'`
**Solution**: 
```bash
chmod +x start_server.sh stop_server.sh check_server.sh
```

#### Port Already in Use
**Error**: `Address already in use`
**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill <process_id>

# Or use different port in .env
PORT=8080
```

#### Module Not Found
**Error**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### OpenAI API Issues
**Error**: `OpenAI API key not found`
**Solution**:
- Check `.env` file exists and contains your API key
- Verify API key is valid at OpenAI platform
- Ensure no extra spaces in the key

### Getting Help

1. **Check Logs**: Always check `logs/server.log` first
2. **Verify Setup**: Ensure all installation steps completed
3. **Test Components**: Test Python, virtual environment, and dependencies
4. **GitHub Issues**: Report persistent issues on GitHub
5. **Community**: Ask questions in discussions

## 🔄 Updating

### Update Application
```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart server
./stop_server.sh
./start_server.sh
```

### Backup Before Updates
```bash
# Backup database
cp magic_cards.db magic_cards.db.backup

# Or use built-in backup
python backup_manager.py --create manual_backup
```

## 🚀 Advanced Setup

### Running as System Service (macOS)

```bash
# Install as system service
sudo ./install_service.sh

# Start service
sudo launchctl load /Library/LaunchDaemons/com.magiccardscanner.server.plist

# Check status
sudo launchctl list | grep magiccardscanner
```

### Running as System Service (Linux)

Create systemd service file:
```bash
sudo nano /etc/systemd/system/magic-card-scanner.service
```

Add service configuration:
```ini
[Unit]
Description=Magic Card Scanner
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/MTG-Scan
ExecStart=/path/to/MTG-Scan/venv/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable magic-card-scanner
sudo systemctl start magic-card-scanner
```

### Docker Setup (Advanced)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t magic-card-scanner .
docker run -p 8000:8000 -v $(pwd)/magic_cards.db:/app/magic_cards.db magic-card-scanner
```

## 📝 Next Steps

After installation:

1. **Read the User Guide**: Check out `USER_GUIDE.md` for detailed feature explanations
2. **Scan Your First Card**: Upload a card image to test the system
3. **Explore Features**: Try different view modes, export options, and settings
4. **Set Up Backups**: Configure automatic backups for your collection
5. **Customize Settings**: Adjust configuration in `.env` file as needed

## 🎉 Success!

If you can access `http://localhost:8000` and see the Magic Card Scanner interface, you're ready to start building your digital collection!

---

**Need help?** Check the [User Guide](USER_GUIDE.md) or create an issue on [GitHub](https://github.com/esbillyjack/MTG-Scan/issues). 