import atexit
import json
import logging
from logging.config import dictConfig
from logging.handlers import QueueHandler, QueueListener

from utils.logkit.settings import (
    LogLevel,
    default_logger_level,
    logging_config_json,
    logs_dir,
    setup_logger_level,
    setup_logger_name,
    validate,
    validate_level
)

_setup_loggin_done: bool = False
_default_queue_listener: QueueListener | None = None
_logger = logging.getLogger(setup_logger_name)
_logger.setLevel(setup_logger_level)





def _setup_logging() -> None:
    global _setup_loggin_done, _default_queue_listener

    if _setup_loggin_done:
        _logger.debug("Logging already configured, doing nothing for now")
        return

    validate()

    if not logging_config_json.is_file():
        msg = f"Logging config file '{logging_config_json}' not found"
        raise FileNotFoundError(msg)

    if not logs_dir.is_dir():
        logs_dir.mkdir(parents=True, exist_ok=True)
        _logger.debug("Created logs directory: %s", logs_dir)

    with logging_config_json.open(mode="r", encoding="utf-8") as file:
        loggin_config = json.load(file)
        _logger.debug("Loaded logging configuration: %s", loggin_config)

    dictConfig(loggin_config)

    queue_handlers = [
        handler for handler in logging.getLogger().handlers
        if isinstance(handler, QueueHandler)
    ]

    queue_handlers_count = len(queue_handlers)
    _logger.debug("QueueHandlers found: %d", queue_handlers_count)

    if queue_handlers_count > 1:
        msg = f"This function does not allow more than one QueuHandler"
        raise RuntimeError(msg)

    if queue_handlers_count > 0:
        queue_handler = queue_handlers[0]
        _logger.debug("Found QueueHandler: %s", queue_handler.name)

        if queue_handler:
            _default_queue_listener = queue_handler.listener

            if _default_queue_listener is not None:
                _default_queue_listener.start()
                atexit.register(_stop_queue_listener)

                _logger.debug("QueueListener from QueueHandler started: %s", _default_queue_listener.name)

                _logger.debug("Function '%s' registered with atexit", _stop_queue_listener.__name__)

    _setup_loggin_done = True


def _stop_queue_listener():
    if _default_queue_listener is None:
        return

    _logger.debug("stopping queue_listener")
    _default_queue_listener.stop()


def get_logger(name: str = "", level: LogLevel | None = None) -> logging.Logger:
    if not _setup_loggin_done:
        _setup_logging()
        _logger.debug("'_setup_loggin_done' used to configure Python logging")
    logger = logging.getLogger(name)

    if level is not None:
        validate_level(level)
        _logger.debug(f"Level: {level!r} used by 'get_logger' to configure {name!r} Logger")
        logger.setLevel(level)

    else:
        env_level = default_logger_level
        _logger.debug(f"Level: {level!r} used by 'ENV' to configure {name!r} Logger")
        logger.setLevel(env_level)

    return logger
