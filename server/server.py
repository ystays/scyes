"""FastAPI server with ngrok integration and Discord interactions."""

import os
import nacl.signing
import nacl.exceptions
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn

from utils import get_random_emoji
from discord import InteractionType, InteractionResponseType
from interactions import (
    handle_challenge_interaction_command,
    handle_interaction_component,
)

from config import app_config

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
