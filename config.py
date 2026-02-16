import os
from dotenv import load_dotenv
import configparser
from pathlib import Path

load_dotenv()  # Load from .env if it exists

class Config:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        if not Path(config_file).exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        self.config.read(config_file)

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
    # API_KEY = os.getenv("API_KEY")
    # DEBUG = os.getenv("DEBUG", "False").lower() == "true"  # Default to False

app_config = Config()