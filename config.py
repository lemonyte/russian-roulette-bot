import os
import sys
from typing import Optional

import yaml

try:
    import dotenv

    dotenv.load_dotenv()
except ModuleNotFoundError:
    pass


class Config:
    def __init__(self, file_path: Optional[str] = None):
        if '--preview' in sys.argv or '-p' in sys.argv:
            self.preview = True

        if not file_path:
            if self.preview:
                file_path = 'config_preview.yaml'
            else:
                file_path = 'config.yaml'

        with open(file_path, 'r') as config_file:
            config_data = yaml.safe_load(config_file)

        self.name: str = config_data.get('name', '')
        self.url: str = config_data.get('url', '')
        self.color: int = config_data.get('color', 0x000000)

        self.prefixes: list[str] = config_data.get('prefixes', [])
        if not self.prefixes:
            raise ValueError("'prefixes' config field must be a non-empty list")

        self.luck_messages: list[str] = config_data.get('luck_messages', [])
        if not self.luck_messages:
            raise ValueError("'luck_messages' config field must be a non-empty list")

        self.death_messages: list[str] = config_data.get('death_messages', [])
        if not self.death_messages:
            raise ValueError("'death_messages' config field must be a non-empty list")

        if self.preview:
            discord_token = os.getenv('DISCORD_TOKEN_PREVIEW')
        else:
            discord_token = os.getenv('DISCORD_TOKEN')

        if not discord_token:
            raise ValueError("no Discord token provided")

        self.discord_token = discord_token


config = Config()
