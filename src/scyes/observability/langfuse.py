from scyes.config import app_config
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=app_config.langfuse_public_key,
    secret_key=app_config.langfuse_secret_key,
    base_url=app_config.langfuse_base_url,
)
