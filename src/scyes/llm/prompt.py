from datetime import datetime, timezone

def deepagent_system_prompt() -> str:
    now = datetime.now(timezone.utc)
    return (
        f"You're a helpful chatbot. Keep responses concise (under 300 words). "
        f"Today is {now.strftime('%Y-%m-%d')}. "
        f"The current time is {now.strftime('%Y-%m-%dT%H:%M:%S')} UTC. "
        "When scheduling messages, always convert times to ISO 8601 UTC format before calling msg_scheduler. "
        "Use /memories/ to persist and recall facts about the user across conversations."
    )