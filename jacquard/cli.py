"""`jacquard` command-line tool handling."""

import os
import sys
import logging
import pathlib
import argparse
import functools
import contextlib

import pkg_resources

from jacquard.config import load_config
from jacquard.plugin import plug_all
from jacquard.commands import CommandError
from jacquard.constants import DEFAULT_CONFIG_FILE_PATH

SUBCOMMAND_GROUPS = (
    ('list', "show lists of various topics"),
    ('show', "show items"),
)


def _add_subparsers_from_plugins(subparsers, plugin_group):
    for name, plugin in plug_all(plugin_group):
        command_class = plugin()
        command = command_class()

        command_help = getattr(command, 'help', name)
        is_plumbing = getattr(command, 'plumbing', False)

        if is_plumbing:
            kwargs = {'description': command_help}
        else:
            kwargs = {'description': command_help, 'help': command_help}

        subparser = subparsers.add_parser(name, **kwargs)

        subparser.set_defaults(func=command.handle)
        command.add_arguments(subparser)


def _add_help_command(parser, subparsers):
    subparser = subparsers.add_parser(
        'help',
        description="show this help",
        help="show this help",
    )

    def _help(config, options):
        help_subcommand = list(options.command) + ['--help']
        parser.parse_args(help_subcommand)

    subparser.set_defaults(func=_help)
    subparser.add_argument(
        'command',
        nargs='*',
        help='command to ask about',
    )


@functools.lru_cache()
def _build_argument_parser(cwd=None):
    parser = argparse.ArgumentParser(description="Split testing server")
    parser.add_argument(
        '-v',
        '--verbose',
        help="enable verbose output",
        action='store_const',
        dest='log_level',
        const=logging.INFO,
        default=logging.ERROR,
    )
    parser.add_argument(
        '--debug',
        help="enable debug output (implies -v)",
        action='store_const',
        dest='log_level',
        const=logging.DEBUG,
    )
    parser.add_argument(
        '-c',
        '--config',
        help="config file",
        type=pathlib.Path,
        default=DEFAULT_CONFIG_FILE_PATH,
    )
    parser.add_argument(
        '-V',
        '--version',
        help="show version and exit",
        action='version',
        version=str(pkg_resources.working_set.by_key['jacquard-split']),
    )
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(metavar='command', title='subcommands')

    # Top-level plugins
    _add_subparsers_from_plugins(
        subparsers=subparsers,
        plugin_group='commands',
    )

    # Subcommand plugins
    for subcommand, subcommand_help in SUBCOMMAND_GROUPS:
        subcommand_parser = subparsers.add_parser(
            subcommand,
            help=subcommand_help,
        )
        subsubcommands = subcommand_parser.add_subparsers(
            metavar="subject",
            title="subjects",
        )

        _add_subparsers_from_plugins(
            subparsers=subsubcommands,
            plugin_group='commands.{subcommand}'.format(
                subcommand=subcommand,
            ),
        )

    _add_help_command(parser, subparsers)

    return parser


def argument_parser():
    """
    Generate an argparse `ArgumentParser` for the CLI.

    This will look through all defined `jacquard.commands` entry points for
    subcommands; these are subclasses of `jacquard.commands.BaseCommand`.
    Using this mechanism, plugins can add their own subcommands.
    """
    # We parameterise this by cwd to persuade `lru_cache` that this is
    # important.
    return _build_argument_parser(os.getcwd())


def _configure_process_and_load_config_from_options(
    options,
    override_config=None,
):
    logging.basicConfig(level=options.log_level)

    if options.func is None:
        # Print help where there are no other arguments. Rather than using
        # `print_help` we explicitly use exactly the same mechanism as
        # --help, which ensures that the exit code, and any extra I/O ops
        # such as buffer flushes, are identical.
        argument_parser().parse_args(['--help'])
        # --help exits the process; something extremely weird has happened if
        # we reached this point in execution.
        raise AssertionError("parse_args(--help) returned")

    if override_config is not None:
        return override_config

    try:
        return load_config(options.config)
    except FileNotFoundError:
        print("Could not read config file '{path}'".format(
            path=options.config,
        ))
        sys.exit(1)


def main(args=sys.argv[1:], config=None):
    """
    Run as if from the command line, with the given arguments.

    If the arguments in `args` are not given they default to using `sys.argv`.

    Note that this function is permitted to raise SystemExit; users who do not
    want exciting exiting behaviour should be prepared to catch this.

    If `config` is given, it is used in place of loading a configuration file.
    """
    parser = argument_parser()
    options = parser.parse_args(args)

    config = _configure_process_and_load_config_from_options(
        options=options,
        override_config=config,
    )

    # Run subcommand
    with contextlib.suppress(KeyboardInterrupt):
        try:
            options.func(config, options)
        except CommandError as exc:
            (message,) = exc.args
            print(message, file=sys.stderr)
            exit(1)
