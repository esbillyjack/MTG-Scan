#!/usr/bin/env python3
"""
Main entry point for Magic Card Scanner - Railway Deployment
"""
import os
import sys

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def main():
    try:
        # Import after setting up path
        from app import app
        import uvicorn
        
        # Get port from environment (Railway sets this)
        port = int(os.environ.get("PORT", 8000))
        
        print(f"Starting Magic Card Scanner on port {port}")
        
        # Run the application
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"Import error: {e}")
        print(f"Python path: {sys.path}")
        print(f"Backend path exists: {os.path.exists(backend_path)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 