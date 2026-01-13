import random


def get_random_emoji():
    """Return a random emoji from the list."""
    emoji_list = ["😭", "😄", "😌", "🤓", "😎", "😤", "🤖", "😶‍🌫️", "🌏", "📸", "💿", "👋", "🌊", "✨"]
    return random.choice(emoji_list)


def capitalize(text):
    """Capitalize first letter of string."""
    return text[0].upper() + text[1:] if len(text) > 0 else text
