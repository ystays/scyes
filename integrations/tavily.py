from langchain_tavily import TavilySearch
from config import app_config

tool = TavilySearch(
    max_results=2,
    topic="general",
    tavily_api_key=app_config.tavily_api_key
    # include_answer=False,
    # include_raw_content=False,
    # include_images=False,
    # include_image_descriptions=False,
    # search_depth="basic",
    # time_range="day",
    # start_date=None,
    # end_date=None,
    # include_domains=None,
    # exclude_domains=None,
    # include_usage= False
)
