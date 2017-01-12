import sys
import pathlib
import argparse
import pkg_resources

from jacquard.config import load_config


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


if '__name__' == '__main__':
    main()
