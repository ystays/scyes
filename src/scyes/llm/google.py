from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
from scyes.config import app_config


def is_unavailable(e: Exception) -> bool:
    return "503" in str(e) or "UNAVAILABLE" in str(e)

GEMINI_3_FLASH = "gemini-3-flash-preview"
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_3_1_FLASH_LITE = "gemini-3.1-flash-lite"
GEMMA_4_31B = "gemma-4-31b-it"

google_model = ChatGoogleGenerativeAI(
    google_api_key=app_config.google_api_key,
    model=GEMINI_3_1_FLASH_LITE,
    temperature=1.0,  # Gemini 3.0+ defaults to 1.0
    max_tokens=None,
    timeout=None,
    max_retries=0,
)

gemini_3_flash_model = ChatGoogleGenerativeAI(
    google_api_key=app_config.google_api_key,
    model=GEMINI_3_FLASH,
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    max_retries=0,
)

gemma_4_31b_model = ChatGoogleGenerativeAI(
    google_api_key=app_config.google_api_key,
    model=GEMMA_4_31B,
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    max_retries=0,
)

gemini_2_5_flash_model = ChatGoogleGenerativeAI(
    google_api_key=app_config.google_api_key,
    model=GEMINI_2_5_FLASH,
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    max_retries=0,
)

# Ordered fallback list for pydantic_ai agents
GOOGLE_FALLBACK_MODELS = [GEMINI_3_1_FLASH_LITE, GEMINI_3_FLASH, GEMMA_4_31B]

# Ordered fallback list for langchain agents
langchain_fallback_models = [google_model, gemini_3_flash_model, gemma_4_31b_model]

GROK_4_1_FAST = "grok-4.1-fast-non-reasoning"

vercel_ai_gateway_model = ChatXAI(
    model=GROK_4_1_FAST,
    temperature=0.5,
    api_key=app_config.vercel_ai_gateway_api_key,
    model_kwargs={"base_url": "https://ai-gateway.vercel.sh/v1"},
)
