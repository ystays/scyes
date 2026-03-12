from datetime import datetime
import dateparser

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # noqa: F401 (used for type hint)
from langchain_core.tools import tool


def create_msg_scheduler_tool(bot, channel_id: int, scheduler: AsyncIOScheduler):
    async def _send_message(text: str, cid: int):
        channel = bot.get_channel(cid) or await bot.fetch_channel(cid)
        await channel.send(f"[Scheduled] {text}")

    @tool
    def msg_scheduler(msg_text: str, remind_at: str) -> str:
        """Schedule a reminder message in the current Discord channel.
        Convert natural language times to ISO 8601 (e.g. '2026-03-10T21:00:00') before calling."""
        try:
            fire_time = datetime.fromisoformat(remind_at)
        except ValueError:
            fire_time = dateparser.parse(remind_at)
            if fire_time is None:
                return f"Could not parse time: {remind_at!r}"

        scheduler.add_job(
            _send_message,
            trigger="date",
            run_date=fire_time,
            args=[msg_text, channel_id],
            misfire_grace_time=60,
        )
        return f"Message scheduled for {fire_time.isoformat()}: '{msg_text}'"

    return msg_scheduler
