"""Structured logging configuration using Rich."""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

# Global console for rich output
console = Console()


def setup_logger(
    name: str = "ia_trading",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a structured logger with Rich formatting.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging to file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Rich console handler for terminal output
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    rich_handler.setLevel(logging.DEBUG)
    logger.addHandler(rich_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Default logger instance
logger = setup_logger()


def log_news_analysis(ticker: str, title: str, sentiment: str, index: int, total: int):
    """Log a news analysis result in a structured format."""
    logger.info(
        f"[bold blue]Analysis {index}/{total}[/bold blue] | "
        f"[cyan]{ticker}[/cyan] | "
        f"Sentiment: [bold]{sentiment}[/bold]"
    )


def log_api_call(service: str, endpoint: str, status: str = "success"):
    """Log an API call."""
    color = "green" if status == "success" else "red"
    logger.debug(f"API [{service}] {endpoint} - [{color}]{status}[/{color}]")


def log_error(message: str, exc: Optional[Exception] = None):
    """Log an error with optional exception details."""
    if exc:
        logger.error(f"{message}: {exc}", exc_info=True)
    else:
        logger.error(message)


def log_warning(message: str):
    """Log a warning message."""
    logger.warning(f"[yellow]{message}[/yellow]")


def log_success(message: str):
    """Log a success message."""
    logger.info(f"[green]{message}[/green]")
