"""
Logging configuration and utilities
"""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    Configura logging global da aplicação.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        format_string: Formato personalizado para logs
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Obtém logger configurado.

    Args:
        name: Nome do logger (normalmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


class ColoredFormatter(logging.Formatter):
    """Formatter que adiciona cores aos logs"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_colored_logging(level: str = "INFO") -> None:
    """Configura logging com cores"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Adiciona handler colorido
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
