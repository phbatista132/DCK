import atexit
import json
import logging
from logging.config import dictConfig
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

from src.utils.logKit.settings import (
    LogLevel,
    default_logger_level,
    logging_config_json,
    logs_dir,
    setup_logger_level,
    setup_logger_name,
    validate_level,
)

_setup_logging_done: bool = False
_default_queue_listener: QueueListener | None = None

_logger = logging.getLogger(setup_logger_name)
_logger.setLevel(setup_logger_level)


def _get_default_config() -> dict:
    """
    Retorna configuração padrão de logging caso o arquivo não exista
    Configuração minimalista para Railway
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(levelname)s|%(name)s|%(asctime)s|%(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
                "level": "INFO"
            }
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO"
        }
    }


def _setup_logging() -> None:
    global _setup_logging_done, _default_queue_listener

    if _setup_logging_done:
        _logger.debug("logging already configured, doing nothing for now")
        return

    # Criar logs_dir se não existir
    try:
        if not logs_dir.is_dir():
            logs_dir.mkdir(parents=True, exist_ok=True)
            _logger.debug("Logs directory created: %s", logs_dir)
    except Exception as e:
        _logger.warning(f"Could not create logs dir: {e}")

    # Tentar carregar configuração do arquivo
    logging_config = None
    if logging_config_json and isinstance(logging_config_json, Path) and logging_config_json.is_file():
        try:
            with logging_config_json.open("r", encoding="utf-8") as file:
                logging_config = json.load(file)
                _logger.debug("JSON config file loaded: %s", logging_config_json)
        except Exception as e:
            _logger.warning(f"Could not load config file: {e}")

    # Se não conseguiu carregar, usar configuração padrão
    if logging_config is None:
        _logger.info("Using default logging config (Railway compatible)")
        logging_config = _get_default_config()

    try:
        dictConfig(logging_config)
    except Exception as e:
        _logger.error(f"Error configuring logging: {e}")
        # Fallback para configuração mínima
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s|%(name)s|%(asctime)s|%(message)s'
        )

    # Configurar QueueHandler se existir
    try:
        queue_handlers = [
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, QueueHandler)
        ]

        queue_handlers_count = len(queue_handlers)
        _logger.debug("QueueHandlers found: %d", queue_handlers_count)

        if queue_handlers_count > 1:
            msg = "This function does not allow more than one QueueHandler"
            raise RuntimeError(msg)

        if queue_handlers_count > 0:
            queue_handler = queue_handlers[0]
            _logger.debug("Found QueueHandler with name: '%s'", queue_handler.name)

            if queue_handler:
                _default_queue_listener = queue_handler.listener

                if _default_queue_listener is not None:
                    _default_queue_listener.start()
                    atexit.register(_stop_queue_listener)

                    _logger.debug(
                        "QueueListener from QueueHandler '%s' started", queue_handler.name
                    )

                    _logger.debug(
                        "Function '%s' registered with atexit",
                        _stop_queue_listener.__name__,
                    )
    except Exception as e:
        _logger.warning(f"Could not setup QueueHandler: {e}")

    _setup_logging_done = True


def _stop_queue_listener() -> None:
    if _default_queue_listener is None:
        return

    _logger.debug("Default listener will stop now, 👋 bye...")
    _default_queue_listener.stop()


def get_logger(name: str = "", level: LogLevel | None = None) -> logging.Logger:
    """
    Obtém um logger configurado

    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger configurado
    """
    if not _setup_logging_done:
        try:
            _setup_logging()
            _logger.debug("'_setup_logging' used to configure Python logging.")
        except Exception as e:
            # Se falhar, usar configuração básica
            logging.basicConfig(
                level=logging.INFO,
                format='%(levelname)s|%(name)s|%(asctime)s|%(message)s'
            )
            _logger.warning(f"Failed to setup logging, using basicConfig: {e}")

    logger = logging.getLogger(name)

    if level is not None:
        try:
            validate_level(level)
            _logger.debug(
                f"Level {level!r} used by 'get_logger' to configure {name!r} logger."
            )
            logger.setLevel(level)
        except Exception as e:
            _logger.warning(f"Could not set level: {e}")
            logger.setLevel(default_logger_level)
    else:
        env_level = default_logger_level
        _logger.debug(
            f"Level {env_level!r} used by 'ENV' to configure {name!r} logger."
        )
        logger.setLevel(env_level)

    return logger