from pathlib import Path
from typing import Any, Dict

import yaml

from .paths import CONFIG_DIR
from .logger import get_logger

logger = get_logger(__name__)


def load_config(filename: str = "settings.yaml") -> Dict[str, Any]:
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info("Config loaded from %s", config_path)
    return config
