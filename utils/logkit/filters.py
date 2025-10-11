import logging


class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: str) -> None:
        # max_level é argumeto adicional e obrigatorio
        # max_level deve receber o nome do level
        super().__init__()

        # Self.max_level terá o numero do level
        self.max_level = logging.getLevelNamesMapping().get(max_level.upper())


    def filter(self, record: logging.LogRecord) -> bool:
        # Filtro do level
        return record.levelno <= self.max_level
