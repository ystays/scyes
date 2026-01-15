"""FastAPI server with ngrok integration and Discord interactions."""
import os
import nacl.signing
import nacl.exceptions
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn

from utils import get_random_emoji
from discord import InteractionType, InteractionResponseType
from interactions import handle_challenge_interaction_command, handle_interaction_component

import logging

# Load environment variables
load_dotenv()

app = FastAPI(title="My API Server")

# Discord verification
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
verify_key = nacl.signing.VerifyKey(bytes.fromhex(PUBLIC_KEY)) if PUBLIC_KEY else None


def verify_discord_request(raw_body: bytes, signature: str, timestamp: str) -> bool:
    """Verify Discord interaction signature."""
    if not verify_key:
        return False
    try:
        verify_key.verify(f"{timestamp}{raw_body.decode()}".encode(), bytes.fromhex(signature))
        return True
    except nacl.exceptions.BadSignatureError:
        return False


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
        "description": "A simple FastAPI server exposed with ngrok"
    }


@app.post("/api/echo")
async def echo(message: str):
    """Echo the message back."""
    return {"echo": message, "received": True}


@app.post("/interactions")
async def interactions(request: Request):
    """Handle Discord interactions webhook."""
    # Get raw body for signature verification
    raw_body = await request.body()
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")

    # Verify request
    if not verify_discord_request(raw_body, signature, timestamp):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.json()
    interaction_type = InteractionType(body.get("type"))
    interaction_id = body.get("id")
    data: dict = body.get("data", {})

    # Handle PING (verification request)
    if interaction_type == InteractionType.ping:
        return {"type": InteractionResponseType.pong.value}

    # Handle APPLICATION_COMMAND
    if interaction_type == InteractionType.application_command:
        command_name: str = data.get("name", "")

        match command_name:
            case "test":
                logging.info("[interactions] Test command")
                return {
                    "type": InteractionResponseType.channel_message.value,
                    "data": {
                        "content": f"hello world {get_random_emoji()}"
                    }
                }

            case "challenge":
                user_id: str = body.get("member", {}).get("user", {}).get("id") or body.get("user", {}).get("id")
                object_name: str = data.get("options", [{}])[0].get("value", "").lower()

                return handle_challenge_interaction_command(user_id, object_name, interaction_id)

            case _:
                logging.warning("[interactions] Invalid command")
                return {"type": InteractionResponseType.channel_message.value, "data": {"content": f"Unknown command: {command_name}"}}

    # Handle MESSAGE_COMPONENT (buttons, select menus)
    if interaction_type == InteractionType.component:
        logging.info("[interactions] Message component interaction")
        custom_id = data.get("custom_id", "")
        resp = handle_interaction_component(custom_id, body, data)
        if resp:
            return resp

    return {
        "type": InteractionResponseType.channel_message.value, 
        "data": {
            "content": "Unknown interaction type"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
