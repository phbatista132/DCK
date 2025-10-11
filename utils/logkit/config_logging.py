import atexit
import json
import logging
from logging.config import dictConfig
from logging.handlers import QueueHandler, QueueListener
from typing import Optional

from utils.logkit.settings import (
    LogLevel,
    default_logger_level,
    logging_config_json,
    logs_dir,
    setup_logger_level,
    setup_logger_name,
    validate,
    validate_level,
)

_setup_logging_done: bool = False
_default_queue_listener: Optional[QueueListener] = None
_logger = logging.getLogger(setup_logger_name)
_logger.setLevel(setup_logger_level)


def _setup_logging() -> None:
    global _setup_logging_done, _default_queue_listener

    if _setup_logging_done:
        _logger.debug("Logging already configured, doing nothing")
        return

    # validate settings (will raise if logging_config_json not found)
    validate()

    if not logging_config_json.is_file():
        msg = f"Logging config file '{logging_config_json}' not found"
        raise FileNotFoundError(msg)

    # ensure logs dir exists
    if not logs_dir.is_dir():
        logs_dir.mkdir(parents=True, exist_ok=True)
        _logger.debug("Created logs directory: %s", logs_dir)

    with logging_config_json.open(mode="r", encoding="utf-8") as file:
        logging_config = json.load(file)
        _logger.debug("Loaded logging configuration: %s", logging_config)

    # Configure logging using dictConfig
    dictConfig(logging_config)

    # Find QueueHandler instances attached to root logger
    queue_handlers = [h for h in logging.getLogger().handlers if isinstance(h, QueueHandler)]
    queue_handlers_count = len(queue_handlers)
    _logger.debug("QueueHandlers found: %d", queue_handlers_count)

    if queue_handlers_count > 1:
        msg = "This function does not allow more than one QueueHandler"
        raise RuntimeError(msg)

    # Build a QueueListener if a QueueHandler is present
    if queue_handlers_count == 1:
        queue_handler = queue_handlers[0]
        # queue object used by QueueHandler
        q = getattr(queue_handler, "queue", None)
        if q is None:
            raise RuntimeError("Found a QueueHandler but it does not expose a 'queue' attribute")

        # Handlers that will actually do the IO (e.g., FileHandler)
        non_queue_handlers = [h for h in logging.getLogger().handlers if not isinstance(h, QueueHandler)]
        if not non_queue_handlers:
            _logger.warning("No non-queue handlers found to attach to QueueListener; logs may be lost")

        # Create and start listener
        _default_queue_listener = QueueListener(q, *non_queue_handlers, respect_handler_level=True)
        _default_queue_listener.start()
        atexit.register(_stop_queue_listener)
        _logger.debug("QueueListener started: %s", getattr(_default_queue_listener, "name", "<unnamed>"))

    _setup_logging_done = True


def _stop_queue_listener() -> None:
    global _default_queue_listener
    if _default_queue_listener is None:
        return
    _logger.debug("Stopping queue listener")
    _default_queue_listener.stop()


def get_logger(name: str = "", level: LogLevel | None = None) -> logging.Logger:
    if not _setup_logging_done:
        _setup_logging()
        _logger.debug("'_setup_logging' used to configure Python logging")
    logger = logging.getLogger(name)

    if level is not None:
        validate_level(level)
        _logger.debug("Level: %r used by 'get_logger' to configure %r Logger", level, name)
        logger.setLevel(level)
    else:
        env_level = default_logger_level
        _logger.debug("Level from ENV used to configure %r Logger: %r", name, env_level)
        logger.setLevel(env_level)

    return logger