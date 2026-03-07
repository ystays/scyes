from langchain.tools import tool
import requests
from config import app_config


@tool
def weather(location: str) -> str:
    """Get current weather conditions for a city or location."""
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": app_config.openweather_api_key,
        "units": "metric"
    }
    data = requests.get(
        url,
        params=params,
        timeout=10,
    ).json()

    return f"{data['name']}: {data['weather'][0]['description']}, {data['main']['temp']}°C, feels like {data['main']['feels_like']}°C"
