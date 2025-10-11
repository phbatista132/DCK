import logging
import json
from datetime import datetime
from typing import Any, override
from zoneinfo import ZoneInfo

TZ_IDENTIFIER = "America/Sao_Paulo"
TZ = ZoneInfo(TZ_IDENTIFIER)

LOG_RECORD_KEYS = [
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
    "message",
]


class JSONLogFormatter(logging.Formatter):
    def __init__(self, include_keys: list[str] | None = None, datefmt: str = "%Y-%m-%dT%H:%M:%S%z") -> None:
        super().__init__()
        self.include_keys = (include_keys if include_keys is not None else LOG_RECORD_KEYS)
        self.datefmt = datefmt

    @override
    def format(self, record: logging.LogRecord) -> str:
        dict_record: dict[str, Any] = {
            key: getattr(record, key) for key in self.include_keys
            if key in LOG_RECORD_KEYS and getattr(record, key, None) is not None
        }

        if "created" in dict_record:
            # Sobrescreve metodo formatTime para retornar datetime, podendo usar timezone
            dict_record["created"] = self.formatTime(record, self.datefmt)

        if "message" in self.include_keys:
            dict_record["message"] = record.getMessage()

        if "exc_info" in dict_record and record.exc_info:
            # formtação para str as informações de exeções
            dict_record["exc_info"] = self.formatException(record.exc_info)

        if "stack_info" in dict_record and record.stack_info:
            # Formatação do valor da stack de exeção para str
            dict_record["stack_info"] = self.formatStack(record.stack_info)

        # caso tenho extras no log
        for key, val in vars(record).items():
            if key in LOG_RECORD_KEYS:
                continue


            if key not in self.include_keys:
                # gera erro caso a chave não esteja sento do include_keys
                msg = f'Key {key!r} does not exist in "include_keys"'
                raise ValueError(msg)

            dict_record[key] = val

        return json.dumps(dict_record)

    @override
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        date = datetime.fromtimestamp(record.created, tz=TZ)
        if datefmt:
            return date.strftime(datefmt)

        return date.isoformat()