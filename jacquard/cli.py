"""`jacquard` command-line tool handling."""

import os
import sys
import logging
import pathlib
import argparse
import contextlib

import pkg_resources

from jacquard.config import load_config
from jacquard.plugin import plug_all
from jacquard.commands import CommandError

DEFAULT_CONFIG_FILE_PATH = pathlib.Path(os.environ.get(
    'JACQUARD_CONFIG',
    '/etc/jacquard/config.cfg',
))


def argument_parser():
    """
    Generate an argparse `ArgumentParser` for the CLI.

    This will look through all defined `jacquard.commands` entry points for
    subcommands; these are subclasses of `jacquard.commands.BaseCommand`.
    Using this mechanism, plugins can add their own subcommands.
    """
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

    for name, plugin in plug_all('commands'):
        command = plugin()()

        command_help = getattr(command, 'help', name)
        is_plumbing = getattr(command, 'plumbing', False)

        if is_plumbing:
            kwargs = {'description': command_help}
        else:
            kwargs = {'description': command_help, 'help': command_help}

        subparser = subparsers.add_parser(name, **kwargs)

        subparser.set_defaults(func=command.handle)
        command.add_arguments(subparser)

    return parser


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

    logging.basicConfig(level=options.log_level)

    if options.func is None:
        parser.print_help()
        return

    # Parse options
    if config is None:
        try:
            config = load_config(options.config)
        except FileNotFoundError:
            print("Could not read config file '%s'" % options.config)
            return

    # Run subcommand
    with contextlib.suppress(KeyboardInterrupt):
        try:
            options.func(config, options)
        except CommandError as exc:
            (message,) = exc.args
            sys.stderr.write("%s\n", message)
            exit(1)


if '__name__' == '__main__':
    main()
