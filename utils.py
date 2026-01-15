import random


def get_random_emoji() -> str:
    emoji_list = [
        "😭",
        "😄",
        "😌",
        "🤓",
        "😎",
        "😤",
        "🤖",
        "😶‍🌫️",
        "🌏",
        "📸",
        "💿",
        "👋",
        "🌊",
        "✨",
    ]
    return random.choice(emoji_list)


def capitalize(text: str) -> str:
    """Capitalize first letter of string."""
    return text[0].upper() + text[1:] if len(text) > 0 else text
