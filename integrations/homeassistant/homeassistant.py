from langchain.tools import tool
from requests import get
from config import app_config 

@tool
def home_assistant() -> str:
    """Home Assistant
    """

    url = f"http://{app_config.home_assistant_base_url}:8123/ENDPOINT"
    headers = {
        "Authorization": f"Bearer {app_config.home_assistant_token}",
        "content-type": "application/json",
    }
    response = get(url, headers=headers)
    return response.text