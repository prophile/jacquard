import sys
import pathlib
import argparse
import configparser

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

    return engine


def main(args=sys.argv[1:]):
    options = argument_parser().parse_args(args)

    # Parse options
    storage = load_config(options.config)

    user_id = 339639

    print(get_settings(user_id, storage))

    # Do some dumb storage tests
    with storage.transaction() as store:
        old_version = store.get('version', 0)
        store['version'] = old_version + 1

    with storage.transaction() as store:
        old_version = store.get('version', 0)
        store['version'] = old_version + 1

    with storage.transaction() as store:
        print(store['version'])

    import random
    if random.random() < 0.2:
        with storage.transaction() as store:
            del store['version']
