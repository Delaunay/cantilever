from dataclasses import dataclass

from cantilever.argparse.command import Command



class _(Command):
    def __init__(self) -> None:
        super().__init__('subsubcmd1')

    @dataclass
    class Arguments:
        profile: str = None
        file: str = None
        fail_on_error: bool = False
        col: int = 24


    def execute(self, args) -> int:
        print("I am here")
