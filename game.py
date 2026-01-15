from utils import capitalize
import random


RPS_CHOICES: dict = {
    "rock": {
        "description": "sedimentary, igneous, or perhaps even metamorphic",
        "virus": "outwaits",
        "computer": "smashes",
        "scissors": "crushes",
    },
    "cowboy": {
        "description": "yeehaw~",
        "scissors": "puts away",
        "wumpus": "lassos",
        "rock": "steel-toe kicks",
    },
    "scissors": {
        "description": "careful ! sharp ! edges !!",
        "paper": "cuts",
        "computer": "cuts cord of",
        "virus": "cuts DNA of",
    },
    "virus": {
        "description": "genetic mutation, malware, or something inbetween",
        "cowboy": "infects",
        "computer": "corrupts",
        "wumpus": "infects",
    },
    "computer": {
        "description": "beep boop beep bzzrrhggggg",
        "cowboy": "overwhelms",
        "paper": "uninstalls firmware for",
        "wumpus": "deletes assets for",
    },
    "wumpus": {
        "description": "the purple Discord fella",
        "paper": "draws picture on",
        "rock": "paints cute face on",
        "scissors": "admires own reflection in",
    },
    "paper": {
        "description": "versatile and iconic",
        "virus": "ignores",
        "cowboy": "gives papercut to",
        "rock": "covers",
    },
}


def get_result(p1, p2):
    """Calculate game result between two players."""
    game_result = None

    if RPS_CHOICES[p1["objectName"]] and RPS_CHOICES[p1["objectName"]].get(
        p2["objectName"]
    ):
        # p1 wins
        game_result = {
            "win": p1,
            "lose": p2,
            "verb": RPS_CHOICES[p1["objectName"]][p2["objectName"]],
        }
    elif RPS_CHOICES[p2["objectName"]] and RPS_CHOICES[p2["objectName"]].get(
        p1["objectName"]
    ):
        # p2 wins
        game_result = {
            "win": p2,
            "lose": p1,
            "verb": RPS_CHOICES[p2["objectName"]][p1["objectName"]],
        }
    else:
        # tie
        game_result = {"win": p1, "lose": p2, "verb": "tie"}

    return format_result(game_result)


def format_result(result):
    """Format the game result as a Discord message."""
    win = result["win"]
    lose = result["lose"]
    verb = result["verb"]

    if verb == "tie":
        return f"<@{win['id']}> and <@{lose['id']}> draw with **{win['objectName']}**"
    else:
        return f"<@{win['id']}>'s **{win['objectName']}** {verb} <@{lose['id']}>'s **{lose['objectName']}**"


def get_rps_choices():
    """Get all available RPS choices."""
    return list(RPS_CHOICES.keys())


def get_shuffled_options():
    """Get shuffled options for select menu."""
    choices = get_rps_choices()
    options = []

    for choice in choices:
        options.append(
            {
                "label": capitalize(choice),
                "value": choice.lower(),
                "description": RPS_CHOICES[choice]["description"],
            }
        )

    random.shuffle(options)
    return options
