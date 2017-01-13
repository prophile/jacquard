"""`jacquard` command-line tool handling."""

import sys
import pathlib
import argparse
import pkg_resources

from jacquard.config import load_config


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
        action='store_true',
    )
    parser.add_argument(
        '-c',
        '--config',
        help="config file",
        type=pathlib.Path,
        default=pathlib.Path('config.cfg'),
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

    for entry_point in pkg_resources.iter_entry_points('jacquard.commands'):
        command = entry_point.load()()

        command_help = getattr(command, 'help', entry_point.name)

        plumbing = getattr(command, 'plumbing', False)

        if plumbing:
            kwargs = {'description': command_help}
        else:
            kwargs = {'description': command_help, 'help': command_help}

        subparser = subparsers.add_parser(
            entry_point.name,
            **kwargs
        )

        subparser.set_defaults(func=command.handle)
        command.add_arguments(subparser)

    return parser


def main(args=sys.argv[1:]):
    """
    Run as if from the command line, with the given arguments.

    If the arguments in `args` are not given they default to using `sys.argv`.

    Note that this function is permitted to raise SystemExit; users who do not
    want exciting exiting behaviour should be prepared to catch this.
    """
    parser = argument_parser()
    options = parser.parse_args(args)

    if options.func is None:
        parser.print_help()
        return

    # Parse options
    config = load_config(options.config)

    # Run subcommand
    options.func(config, options)


if '__name__' == '__main__':
    main()
