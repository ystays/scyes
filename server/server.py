"""FastAPI server with ngrok integration and Discord interactions."""

from fastapi import FastAPI
import uvicorn

import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="My API Server")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello!", "status": "running"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api_server"}


@app.get("/api/info")
async def get_info():
    """Get server info."""
    return {
        "name": "scyes",
        "version": "1.0.0",
        "description": "A simple FastAPI server exposed with ngrok",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
