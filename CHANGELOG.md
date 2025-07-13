# Changelog

All notable changes to the Magic Card Scanner project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Mana symbol display for visual mana costs
- Deck building functionality
- Trading tools and want lists
- Mobile app development
- Cloud sync capabilities
- Advanced analytics dashboard

## [2.0.0] - 2024-07-13

### Added
- **Export System**: Complete local export functionality with CSV and Excel formats
- **File Browser Integration**: Select export location and filename with overwrite confirmation
- **Backup System**: Automated backup scheduler with manual backup options
- **Enhanced Documentation**: Comprehensive user guide, installation guide, and features showcase
- **Server Management**: Background process management with PID tracking
- **Environment Configuration**: Template .env file with configuration options
- **Statistics Dashboard**: Real-time collection statistics with accurate counting
- **Card ID Display**: Proper ID handling in card details modal

### Changed
- **Export Default**: CSV format now default instead of both formats
- **Stats System**: Unified statistics system with backend calculations
- **Card Display**: Fixed card count display showing price instead of count
- **Unique ID Handling**: Proper unique_id field handling in stacked view
- **Error Handling**: Improved error messages and user feedback
- **Documentation**: Updated README with current features and capabilities

### Fixed
- **Card Count Display**: Fixed cards showing price instead of count in individual view
- **Stats Inconsistency**: Resolved stats requiring refresh to be accurate
- **Card ID Display**: Fixed card ID showing as 'N/A' in details modal
- **Export Functionality**: Fixed export modal and file selection issues
- **Stacked View**: Fixed unique_id handling in stacked card creation
- **Statistics Updates**: Fixed race condition between stats endpoints

### Security
- **Environment Variables**: Added .env to .gitignore to prevent API key exposure
- **Sensitive Data**: Excluded backup files and test data from repository

## [1.0.0] - 2024-06-XX

### Added
- **AI Card Recognition**: OpenAI Vision API integration for automatic card identification
- **Collection Management**: Individual and stacked view modes for card organization
- **Price Integration**: Real-time price lookup from Scryfall API
- **Soft Deletion**: Safe card deletion with recovery options
- **Search Functionality**: Real-time search across card names and sets
- **Condition Tracking**: Standard Magic card condition management
- **Visual Design**: Authentic Magic card proportions and color identity borders
- **Database System**: SQLite database with UUID tracking and timestamps
- **Web Interface**: Modern, responsive web interface
- **Example System**: Mark cards as examples vs. owned cards

### Technical
- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript with modern CSS
- **Database**: SQLite with soft deletion and UUID support
- **APIs**: OpenAI Vision API and Scryfall API integration
- **Architecture**: RESTful API design with comprehensive endpoints

## [0.1.0] - Initial Development

### Added
- Basic card scanning functionality
- Simple database storage
- Web interface prototype
- AI integration proof of concept

---

## Release Notes

### Version 2.0.0 - "Export & Polish"

This major release focuses on data export capabilities, comprehensive documentation, and user experience improvements. Key highlights include:

**🚀 New Features:**
- Complete export system with CSV/Excel formats and file browser
- Automated backup system with scheduling
- Enhanced statistics dashboard with real-time updates
- Comprehensive documentation suite

**🐛 Bug Fixes:**
- Fixed card count display issues
- Resolved statistics inconsistency problems
- Fixed card ID display in details modal
- Improved error handling throughout

**📚 Documentation:**
- Added comprehensive user guide
- Created detailed installation instructions
- Added features showcase document
- Updated README with current capabilities

**🔧 Technical Improvements:**
- Enhanced server management with PID tracking
- Improved environment configuration
- Better error handling and user feedback
- Unified statistics system

### Version 1.0.0 - "Foundation"

The initial stable release establishing core functionality:

**🎯 Core Features:**
- AI-powered card recognition
- Collection management with multiple views
- Real-time price integration
- Comprehensive search and filtering
- Modern web interface

**🛡️ Data Safety:**
- Soft deletion system
- UUID tracking for all cards
- Comprehensive backup capabilities
- Data integrity protection

**🎨 User Experience:**
- Authentic Magic card display
- Responsive design for all devices
- Intuitive navigation and controls
- Professional visual design

---

## Contributing

When contributing to this project, please:

1. **Update the changelog** for any user-facing changes
2. **Follow semantic versioning** for version numbers
3. **Document breaking changes** clearly
4. **Include migration instructions** when necessary

## Support

For questions about specific versions or changes:
- Check the [User Guide](USER_GUIDE.md) for feature documentation
- Review the [Installation Guide](INSTALLATION.md) for setup issues
- Create an issue on GitHub for bug reports or feature requests 