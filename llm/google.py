from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
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

GROK_4_1_FAST = "grok-4.1-fast-non-reasoning"

vercel_ai_gateway_model = ChatXAI(
    base_url="https://ai-gateway.vercel.sh/v1",
    model=GROK_4_1_FAST,
    temperature=0.5,
    api_key=app_config.vercel_ai_gateway_api_key,
)
