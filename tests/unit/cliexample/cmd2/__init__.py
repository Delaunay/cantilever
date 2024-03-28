from dataclasses import dataclass

from cantilever.argparse.command import ParentCommand



class _(ParentCommand):
    def __init__(self) -> None:
        super().__init__('cmd2')

 
_()

