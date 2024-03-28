from __future__ import annotations

import argparse
import os
from contextlib import contextmanager
from collections import defaultdict

from .argformat import HelpAction
from .argparse import add_arguments
from .plugins import discover_plugins

from cantilever.core.timer import timeit


from contextvars import ContextVar, Context


def newparser(subparsers: argparse._SubParsersAction, commandcls: Command):
    """Add a subparser to the parser for the command"""
    parser = subparsers.add_parser(
        commandcls.name,
        description=commandcls.help(),
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action=HelpAction, help="show this help message and exit"
    )
    return parser


@contextmanager
def chdir(root):
    """change directory and revert back to previous directory"""
    old = os.getcwd()
    os.chdir(root)

    yield
    os.chdir(old)


class _Registry:
    def __init__(self) -> None:
        self.namespaces = []
        self.commands = defaultdict(dict)

    def add(self, instance):
        self.commands[instance.name] = instance

    @contextmanager
    def group(self, name):
        self.namespaces.append(name)
        yield
        self.namespaces.pop()

command_registry = _Registry()


def register_command(cmd):
    global command_registry
    command_registry.add(cmd)


class Command:
    """Base class for all commands"""

    def __init__(self, name) -> None:
        self.name = name
        register_command(self)

    @classmethod
    def help(cls) -> str:
        """Return the help text for the command"""
        return cls.__doc__ or ""

    @classmethod
    def argument_class(cls):
        return cls.Arguments

    @classmethod
    def arguments(cls, subparsers):
        """Define the arguments of this command"""
        with timeit("Command.arguments"):
            parser = newparser(subparsers, cls)
            add_arguments(parser, cls.argument_class())

    def execute(self, args) -> int:
        """Execute the command"""
        raise NotImplementedError()

    @staticmethod
    def examples() -> list[str]:
        """returns a list of examples"""
        return []


class ParentCommand(Command):
    """Loads child module as subcommands"""

    def __init__(self, name) -> None:
        self.name = name
        register_command(self)
    
    @staticmethod
    def module():
        return None

    @staticmethod
    def command_field():
        return "subcommand"

    @classmethod
    def arguments(cls, subparsers):
        parser = newparser(subparsers, cls)
        cls.shared_arguments(parser)
        subparsers = parser.add_subparsers(
            dest=cls.command_field(), help=cls.help()
        )
        cmds = cls.fetch_commands()
        cls.register(cls, subparsers, cmds)

    @classmethod
    def shared_arguments(cls, subparsers):
        pass

    @classmethod
    def fetch_commands(cls):
        """Fetch commands using importlib, assume each command is inside its own module"""
        with timeit(f"{cls.name}.fetch_commands"):
            all_commands = []
            for _, module in discover_plugins(cls.module()).items():
                if hasattr(module, "COMMANDS"):
                    commands = getattr(module, "COMMANDS")

                    if not isinstance(commands, list):
                        commands = [commands]

                    all_commands.extend(commands)
        return all_commands

    @staticmethod
    def register(cls, subsubparsers, commands):
        name = cls.module().__name__
        for cmd in commands:
            cmd.arguments(subsubparsers)
            assert (name, cmd.name) not in cls.dispatch
            cls.dispatch[(name, cmd.name)] = cmd

    @classmethod
    def execute(cls, args):
        cmd = cls.module().__name__
        subcmd = vars(args).pop(cls.command_field())

        cmd = cls.dispatch.get((cmd, subcmd), None)
        if cmd:
            return cmd.execute(args)

        raise RuntimeError(f"Subcommand {cls.name} {subcmd} is not defined")
