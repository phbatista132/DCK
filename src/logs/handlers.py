from rich.console import Console
from rich.logging import RichHandler
from typing import Any, Literal
import sys

class MyRichHandler(RichHandler):
    def __init__(self,file: Literal['stdout', 'stderr'] = 'stdout' ,**kwargs: Any) -> None:
        super().__init__(**kwargs)

        if file not in ['stdout', 'stderr']:
            msg = "MyRichHandler: file need to be stdout or stderr"
            raise ValueError(msg)

        console = Console(file=getattr(sys, file))
        self.console =console