import logging
from logging import Logger
from typing import Optional

# Module-level logger cache
_LOGGER: Optional[Logger] = None


def get_logger(name: str = "etf_agent") -> Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _LOGGER = logger
    return logger
