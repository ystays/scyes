from scyes.config import app_config

HA_MCP_CONFIG = {
    "Home Assistant": {
        "url": f"{app_config.home_assistant_base_url}/api/mcp",
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {app_config.home_assistant_token}"},
    }
}
