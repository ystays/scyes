import logging
from typing import Callable

import discord
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def create_buttons_tool(bot, channel_id: int, on_click: Callable):
    class DynamicView(discord.ui.View):
        def __init__(self, buttons: list[dict]):
            super().__init__(timeout=300)
            for btn in buttons:
                label = btn.get("label", "Button")
                value = btn.get("value", label)
                button = discord.ui.Button(
                    label=label,
                    custom_id=value[:100],
                    style=discord.ButtonStyle.secondary,
                )
                button.callback = self._make_callback(value)
                self.add_item(button)

        def _make_callback(self, value: str):
            async def callback(interaction: discord.Interaction):
                await on_click(interaction, value)

            return callback

    @tool
    async def send_buttons_message(content: str, buttons: list[dict]) -> str:
        """Send a Discord message with interactive buttons.
        Each button is a dict with "label" (display text) and "value" (sent to LLM when clicked).
        The user can click a button to continue the conversation with that value."""
        try:
            channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            view = DynamicView(buttons)
            await channel.send(content, view=view)
            return "Message with buttons sent."
        except Exception as e:
            logger.error(f"Failed to send buttons message: {e}")
            return f"Error sending buttons message: {e}"

    return send_buttons_message
