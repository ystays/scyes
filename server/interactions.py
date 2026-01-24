from discord import InteractionResponseType, ComponentType
from game import get_result, get_shuffled_options
from utils import get_random_emoji
from langchain_ollama import ChatOllama

# Store for in-progress games (message_id -> game_state)
active_games = {}


def handle_challenge_interaction_command(
    user_id: str, object_name: str, interaction_id: str
) -> dict:
    # Store active game
    active_games[interaction_id] = {
        "challenger_id": user_id,
        "challenger_choice": object_name,
    }

    return {
        "type": InteractionResponseType.channel_message.value,
        "data": {
            "content": f"Rock paper scissors challenge from <@{user_id}>",
            "components": [
                {
                    "type": ComponentType.action_row.value,
                    "components": [
                        {
                            "type": ComponentType.button.value,
                            "custom_id": f"accept_button_{interaction_id}",
                            "label": "Accept",
                            "style": 1,
                        }
                    ],
                }
            ],
        },
    }


def handle_accept_button(game_id: str) -> dict:
    return {
        "type": InteractionResponseType.channel_message.value,
        "data": {
            "flags": 64,  # Ephemeral (should be MessageFlags.ephemeral)
            "content": "What is your object of choice?",
            "components": [
                {
                    "type": ComponentType.action_row.value,
                    "components": [
                        {
                            "type": ComponentType.select.value,
                            "custom_id": f"select_choice_{game_id}",
                            "placeholder": "Choose your object...",
                            "options": get_shuffled_options(),
                        }
                    ],
                }
            ],
        },
    }


def handle_interaction_component(custom_id: str, body: dict, data: dict) -> dict | None:
    if custom_id.startswith("accept_button_"):
        game_id = custom_id.replace("accept_button_", "")
        return handle_accept_button(game_id)

    if custom_id.startswith("select_choice_"):
        game_id = custom_id.replace("select_choice_", "")

        if game_id not in active_games:
            return {
                "type": InteractionResponseType.channel_message.value,
                "data": {"content": "This game is no longer active."},
            }

        game = active_games[game_id]
        user_id = body.get("member", {}).get("user", {}).get("id") or body.get(
            "user", {}
        ).get("id")
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
            "type": InteractionResponseType.channel_message.value,
            "data": {"content": f"{result_text}\n\nNice choice {get_random_emoji()}"},
        }

    return None

# Initialize LLM
llm = ChatOllama(
    model="gemma3:4b",
    temperature=0,
)

def handle_llm_command(message: str) -> dict:
    """Handle /llm command by calling the LLM."""
    try:
        response = llm.invoke(message)
        content = response.content
    except Exception as e:
        content = f"Error calling LLM: {str(e)}"

    return {
        "type": InteractionResponseType.channel_message.value,
        "data": {"content": content},
    }
