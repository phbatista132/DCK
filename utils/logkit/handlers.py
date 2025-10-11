import logging
import sys
from typing import Any, Literal

from rich.console import Console
from rich.logging import RichHandler

class MyRichHandler(RichHandler):
    def __init__(self, file: Literal["stdout", "stderr"] = "stdout", **kwargs: Any ) -> None:
        super().__init__(**kwargs)

        if file not in ["stdout", "stderr"]:
            msg = f"MyRichHandler: 'file' needs to be stdout and stderr"
            raise ValueError(msg)

        console =  Console(file=getattr(sys, file))
        self.console = console

    def emit(self, record: logging.LogRecord) -> None:
        return super().emit(record)

