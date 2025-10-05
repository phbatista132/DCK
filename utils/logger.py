from logging.config import dictConfig
import json
from pathlib import Path

ROOT_DIR = Path('.')
LOGGING_CONFIG_JSON = ROOT_DIR / "utils/logging.json"


def setup() -> None:
    if not LOGGING_CONFIG_JSON.is_file():
        msg = f"File {LOGGING_CONFIG_JSON} not exist"
        raise FileNotFoundError(msg)

    with LOGGING_CONFIG_JSON.open('r', encoding='utf-8') as file:
        logging_config = json.load(file)

    dictConfig(logging_config)




