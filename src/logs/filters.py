import logging

class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level) -> None:
        super().__init__()

        self.max_level = logging.getLevelNamesMapping().get(max_level.upper(), 50)

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level
