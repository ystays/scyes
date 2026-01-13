import os
import discord
from discord.ext import commands
from discord import app_commands
import dotenv

from game import get_result, get_rps_choices, get_shuffled_options
from utils import get_random_emoji

import ngrok


# Load environment variables
dotenv.load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Store for in-progress games (message_id -> game_state)
active_games = {}


class ChallengeView(discord.ui.View):
    """View for the challenge accept button."""

    def __init__(self, challenger_id, challenger_choice, message_id):
        super().__init__(timeout=None)
        self.challenger_id = challenger_id
        self.challenger_choice = challenger_choice
        self.message_id = message_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.primary)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle accept button click."""
        # Prevent challenger from accepting their own challenge
        if interaction.user.id == self.challenger_id:
            await interaction.response.send_message(
                "You can't accept your own challenge!",
                ephemeral=True
            )
            return

        # Store game state
        active_games[self.message_id] = {
            "challenger_id": self.challenger_id,
            "challenger_choice": self.challenger_choice,
            "original_message": interaction.message,
        }

        # Show choice select menu
        view = ChoiceView(self.message_id)
        await interaction.response.send_message(
            "What is your object of choice?",
            view=view,
            ephemeral=True
        )


class ChoiceView(discord.ui.View):
    """View for the opponent's choice select menu."""

    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id

        # Add select menu with shuffled options
        select = discord.ui.Select(
            placeholder="Choose your object...",
            options=[
                discord.SelectOption(
                    label=opt["label"],
                    value=opt["value"],
                    description=opt["description"]
                )
                for opt in get_shuffled_options()
            ],
            custom_id=f"choice_select_{message_id}"
        )
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        """Handle opponent's choice selection."""
        if self.message_id not in active_games:
            await interaction.response.send_message(
                "This game is no longer active.",
                ephemeral=True
            )
            return

        game = active_games[self.message_id]
        opponent_choice = interaction.data["values"][0]

        # Calculate result
        challenger = {
            "id": game["challenger_id"],
            "objectName": game["challenger_choice"],
        }
        opponent = {
            "id": interaction.user.id,
            "objectName": opponent_choice,
        }

        result_text = get_result(challenger, opponent)

        # Send result message to channel
        await interaction.response.send_message(result_text)

        # Update original challenge message (remove button)
        try:
            await game["original_message"].edit(view=None)
        except discord.errors.NotFound:
            pass  # Original message was deleted

        # Update the ephemeral choice message
        try:
            await interaction.edit_original_response(
                content=f"Nice choice {get_random_emoji()}"
            )
        except:
            pass  # Message was already responded to

        # Clean up game state
        del active_games[self.message_id]


@bot.event
async def on_ready():
    """Event handler for when bot is ready."""
    print(f"Logged on as {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="test", description="Basic test command")
async def test_command(interaction: discord.Interaction):
    """Test command."""
    await interaction.response.send_message(
        f"hello world {get_random_emoji()}"
    )


@bot.tree.command(name="challenge", description="Challenge to a match of rock paper scissors")
@app_commands.describe(object="Pick your object")
@app_commands.choices(object=[
    app_commands.Choice(name=choice.capitalize(), value=choice)
    for choice in get_rps_choices()
])
async def challenge_command(interaction: discord.Interaction, object: str):
    """Challenge command."""
    # Create challenge message with accept button
    view = ChallengeView(
        challenger_id=interaction.user.id,
        challenger_choice=object.lower(),
        message_id=interaction.id
    )

    await interaction.response.send_message(
        f"Rock paper scissors challenge from <@{interaction.user.id}>",
        view=view
    )


def main():
    """Main entry point."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")
    bot.run(token)


if __name__ == "__main__":
    main()
