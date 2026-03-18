"""Logging configuration."""
import logging
import logging.config
from pathlib import Path


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Load logging config
    config_path = Path(__file__).parent.parent / "logging.conf"
    if config_path.exists():
        logging.config.fileConfig(config_path, disable_existing_loggers=False)
    else:
        # Fallback to basic config
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    logger = logging.getLogger("app")
    logger.info("Logging configured")
    return logger


# Create logger instance
logger = setup_logging()
