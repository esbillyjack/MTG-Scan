# Magic Card Scanner

An AI-powered web application that identifies Magic: The Gathering cards from photos and tracks your collection with advanced features like stacking, soft deletion, detailed card management, and local data export.

## ✨ Features

### Core Functionality
- **AI Card Recognition**: Upload photos and automatically identify MTG cards using OpenAI Vision API
- **Smart Database Tracking**: Store cards with unique IDs, counts, conditions, and timestamps
- **Real-time Price Integration**: Live price lookup from Scryfall API with USD/EUR pricing
- **Soft Deletion Protection**: Cards are safely marked as deleted, not permanently removed

### Advanced Card Management
- **Individual & Stacked Views**: Toggle between seeing all cards individually or grouped by duplicates
- **Visual Stack Effects**: Stacked cards display with mini-fanned visual effects and count badges
- **Condition Tracking**: Track card conditions (Near Mint, Lightly Played, etc.) with price impact
- **Example Card System**: Mark cards as examples vs. owned cards with visual indicators
- **Duplicate Grouping**: Intelligent grouping of identical cards with proper count tracking

### Data Export & Backup
- **Local Export**: Export collection to CSV or Excel formats with custom formatting
- **File Browser Integration**: Select export location and filename with overwrite confirmation
- **Automatic Backups**: Scheduled database backups with timestamp management
- **Comprehensive Data**: Export includes all card details, conditions, prices, and notes

### Modern User Interface
- **Proper Magic Card Proportions**: Cards display in authentic 2.5:3.5 ratio
- **Color-Coded Borders**: Cards show color identity borders (White, Blue, Black, Red, Green, Multicolor, Colorless)
- **Responsive Design**: Works on desktop and mobile devices
- **Drag-and-Drop Upload**: Modern file upload with progress tracking
- **Enhanced Detail Modals**: Comprehensive card detail views with navigation and editing

### Collection Features
- **Search & Filter**: Find cards by name or set with real-time filtering
- **Navigation Arrows**: Browse through cards with keyboard/click navigation
- **Statistics Dashboard**: Track total cards, counts, and collection value with real-time updates
- **Set & Rarity Management**: Update card sets and rarities with comprehensive dropdowns
- **Card Notes**: Add personal notes to cards for tracking purposes

## 🛠 Tech Stack

- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Frontend**: Modern HTML/CSS/JavaScript with responsive design
- **Database**: SQLite with soft deletion and UUID tracking
- **AI**: OpenAI Vision API for card recognition
- **Price API**: Scryfall API for comprehensive card data
- **Export**: Pandas and OpenPyXL for data export functionality
- **Server Management**: Background process management with PID tracking

## 📁 Project Structure

```
magic-card-scanner/
├── backend/
│   ├── app.py                    # FastAPI application with all endpoints
│   ├── database.py               # Database models with UUID and soft delete
│   ├── ai_processor.py           # AI card recognition engine
│   ├── price_api.py              # Scryfall API integration
│   ├── image_quality_validator.py # Image validation
│   └── set_symbol_validator.py   # Set symbol validation
├── frontend/
│   ├── index.html                # Main application interface
│   ├── script.js                 # Frontend logic and interactions
│   └── styles.css                # Responsive CSS with card styling
├── export_local.py               # Local export functionality
├── backup_manager.py             # Database backup system
├── auto_backup.py                # Automated backup scheduler
├── start_server.sh               # Server startup script
├── stop_server.sh                # Server shutdown script
├── check_server.sh               # Server status checker
└── requirements.txt              # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/esbillyjack/MTG-Scan.git
   cd MTG-Scan
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Start the server**
   ```bash
   ./start_server.sh
   ```

6. **Access the application**
   - Open your browser to `http://localhost:8000`
   - Start scanning your Magic cards!

### Server Management

- **Start server**: `./start_server.sh`
- **Stop server**: `./stop_server.sh`
- **Check status**: `./check_server.sh`
- **View logs**: `tail -f logs/server.log`

## 📖 User Guide

For a comprehensive guide with screenshots and detailed feature explanations, see the [User Guide](USER_GUIDE.md).

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key for card recognition
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `BACKUP_INTERVAL`: Automatic backup interval in hours (default: 6)

### Database
The application uses SQLite by default with the following features:
- Soft deletion (cards marked as deleted, not removed)
- UUID tracking for unique identification
- Automatic timestamps for all operations
- Comprehensive card metadata storage

## 🛡️ Data Safety

The application includes multiple data protection features:
- **Soft deletion**: Cards are never permanently removed
- **Automatic backups**: Regular database backups with timestamps
- **Local storage**: All data stays on your machine
- **Export functionality**: Easy data export for external backup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the Vision API
- Scryfall for the comprehensive MTG database
- The Magic: The Gathering community for inspiration

## 📊 Current Status

- ✅ Core card recognition and storage
- ✅ Advanced UI with stacking and visual effects
- ✅ Comprehensive export functionality
- ✅ Automated backup system
- ✅ Server management tools
- ✅ Real-time statistics and filtering
- 🔄 Ongoing improvements and feature additions

---

**Note**: This application is for personal use in tracking your Magic: The Gathering collection. It is not affiliated with Wizards of the Coast. 