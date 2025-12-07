#!/usr/bin/env python3
"""
Entry point for Google Cloud Buildpacks
This file is used when buildpacks are used instead of Dockerfile
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from src.api.main import app
    
    # Get port from environment variable (Cloud Run sets this)
    port = int(os.environ.get("PORT", 8080))
    
    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


