import sys
import pathlib
import argparse
import configparser
import pkg_resources

from jacquard.storage import open_engine
from jacquard.users import get_settings


def argument_parser():
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
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(metavar='subcommand')

    for entry_point in pkg_resources.iter_entry_points('jacquard.commands'):
        command = entry_point.load()()

        command_help = getattr(entry_point, 'help', entry_point.name)

        subparser = subparsers.add_parser(
            entry_point.name,
            help=command_help,
            description=command_help,
        )

        subparser.set_defaults(func=command.handle)

        command.add_arguments(subparser)

    return parser


def load_config(config_file):
    parser = configparser.ConfigParser()

    with config_file.open('r') as f:
        parser.read_file(f)

    # Get storage engine
    engine = open_engine(
        engine=parser.get('storage', 'engine'),
        url=parser.get('storage', 'url'),
    )

    return {
        'storage': engine,
    }


def main(args=sys.argv[1:]):
    parser = argument_parser()
    options = parser.parse_args(args)

    if options.func is None:
        parser.print_usage()
        return

    # Parse options
    config = load_config(options.config)

    # Run subcommand
    options.func(config, options)
