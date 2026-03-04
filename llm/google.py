from langchain_google_genai import ChatGoogleGenerativeAI
from config import app_config

GEMINI_3_FLASH = "gemini-3-flash-preview"
GEMINI_2_5_FLASH = "gemini-2.5-flash"

google_model = ChatGoogleGenerativeAI(
    google_api_key=app_config.google_api_key, 
    model=GEMINI_2_5_FLASH,
    temperature=1.0,  # Gemini 3.0+ defaults to 1.0
    max_tokens=None,
    timeout=None,
    max_retries=0,
    # other params...
)