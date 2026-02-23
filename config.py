import configparser
from pathlib import Path


class Config:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        if not Path(config_file).exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        self.config.read(config_file)

        self.environment: str = "dev"

        self.logging_level: str = self.config['logging'].get("level")
        self.logging_file: str = self.config['logging'].get("file")

        self.discord_app_id: str = self.config['discord'].get("APP_ID")
        self.discord_token: str = self.config['discord'].get("DISCORD_TOKEN")
        self.discord_public_key: str = self.config['discord'].get("PUBLIC_KEY")

        self.langfuse_secret_key: str = self.config['langfuse'].get("LANGFUSE_SECRET_KEY")
        self.langfuse_public_key: str = self.config['langfuse'].get("LANGFUSE_PUBLIC_KEY")
        self.langfuse_base_url: str = self.config['langfuse'].get("LANGFUSE_BASE_URL")

        self.tavily_api_key: str = self.config['tavily'].get("TAVILY_API_KEY")

        self.home_assistant_base_url: str = self.config['homeassistant'].get("HOME_ASSISTANT_BASE_URL")
        self.home_assistant_token: str = self.config['homeassistant'].get("HOME_ASSISTANT_TOKEN")

        self.google_api_key: str = self.config['google'].get('GOOGLE_API_KEY')

        self.otel_enabled: bool = self.config['otel'].get('ENABLED', 'false') == 'true'
        self.otel_service_name: str = self.config['otel'].get('SERVICE_NAME', 'scyes')
        self.otel_collector_endpoint: str = self.config['otel'].get('OTLP_HTTP_ENDPOINT', 'http://localhost:4318')

    def get_database_config(self):
        db = self.config['database']
        return {
            'host': db.get('host'),
            'port': db.getint('port'),
            'username': db.get('username'),
            'password': db.get('password'),
            'pool_size': db.getint('pool_size', fallback=5)
        }

    # DATABASE_URL = os.getenv("DATABASE_URL")
    # DEBUG = os.getenv("DEBUG", "False").lower() == "true"  # Default to False

app_config = Config()