import logging
from datetime import datetime, UTC
from typing import Any
from typing_extensions import override

LOG_RECORD_KEYS = ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'exc_info',
                   'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread',
                   'threadName', 'processName', 'process', 'taskName']


class JSONLogFormatter(logging.Formatter):
    def __init__(self, include_keys: list[str] | None = None) -> None:
        super().__init__()
        self.include_keys = include_keys if include_keys is not None else LOG_RECORD_KEYS

    @override
    def format(self, record: logging.LogRecord) -> str:
        dict_record: dict[str, Any] = {
            key: getattr(record, key) for key in self.include_keys
            if key in LOG_RECORD_KEYS and getattr(record, key) is not None

        }

        return ''

    @override
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        date = datetime.fromtimestamp(record.created, tz=UTC)
        if datefmt:
            return date.strftime(datefmt)

        return date.isoformat()
