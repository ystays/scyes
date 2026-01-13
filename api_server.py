"""FastAPI server with ngrok integration and Discord interactions."""
import os
import nacl.signing
import nacl.exceptions
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn

from game import get_result, get_shuffled_options
from utils import get_random_emoji

# Load environment variables
load_dotenv()

app = FastAPI(title="My API Server")

# Store for in-progress games (message_id -> game_state)
active_games = {}

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
    return {"message": "Hello from FastAPI!", "status": "running"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api_server"}


@app.get("/api/info")
async def get_info():
    """Get server info."""
    return {
        "name": "My FastAPI Server",
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
    interaction_type = body.get("type")
    interaction_id = body.get("id")
    data = body.get("data", {})

    # Handle PING (verification request)
    if interaction_type == 1:
        return {"type": 1}

    # Handle APPLICATION_COMMAND
    if interaction_type == 2:
        command_name = data.get("name")

        if command_name == "test":
            return {
                "type": 4,
                "data": {
                    "content": f"hello world {get_random_emoji()}"
                }
            }

        if command_name == "challenge":
            user_id = body.get("member", {}).get("user", {}).get("id") or body.get("user", {}).get("id")
            object_name = data.get("options", [{}])[0].get("value", "").lower()

            # Store active game
            active_games[interaction_id] = {
                "challenger_id": user_id,
                "challenger_choice": object_name,
            }

            return {
                "type": 4,
                "data": {
                    "content": f"Rock paper scissors challenge from <@{user_id}>",
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 2,
                                    "custom_id": f"accept_button_{interaction_id}",
                                    "label": "Accept",
                                    "style": 1,
                                }
                            ]
                        }
                    ]
                }
            }

        return {"type": 4, "data": {"content": f"Unknown command: {command_name}"}}

    # Handle MESSAGE_COMPONENT (buttons, select menus)
    if interaction_type == 3:
        custom_id = data.get("custom_id", "")

        if custom_id.startswith("accept_button_"):
            game_id = custom_id.replace("accept_button_", "")

            return {
                "type": 4,
                "data": {
                    "flags": 64,  # Ephemeral
                    "content": "What is your object of choice?",
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 3,
                                    "custom_id": f"select_choice_{game_id}",
                                    "placeholder": "Choose your object...",
                                    "options": get_shuffled_options()
                                }
                            ]
                        }
                    ]
                }
            }

        if custom_id.startswith("select_choice_"):
            game_id = custom_id.replace("select_choice_", "")

            if game_id not in active_games:
                return {"type": 4, "data": {"content": "This game is no longer active."}}

            game = active_games[game_id]
            user_id = body.get("member", {}).get("user", {}).get("id") or body.get("user", {}).get("id")
            opponent_choice = data.get("values", [""])[0]

            challenger = {
                "id": game["challenger_id"],
                "objectName": game["challenger_choice"],
            }
            opponent = {
                "id": user_id,
                "objectName": opponent_choice,
            }

            result_text = get_result(challenger, opponent)
            del active_games[game_id]

            return {
                "type": 4,
                "data": {
                    "content": f"{result_text}\n\nNice choice {get_random_emoji()}"
                }
            }

    return {"type": 4, "data": {"content": "Unknown interaction type"}}


if __name__ == "__main__":
    # Run the server on localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
