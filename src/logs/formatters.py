import logging

LOG_RECORD_KEYS = [ 'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'exc_info',
                     'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread',
                     'threadName', 'processName', 'process', 'taskName']


class JSONLogFormatter(logging.Formatter):
    def __init__(self, include_keys: list[str] | None = None) -> None:
        super().__init__()
        self.include_keys = include_keys

    def format(self, record: logging.LogRecord) -> str:
        from rich import print as rprint
        rprint(vars(record))
        return ''
