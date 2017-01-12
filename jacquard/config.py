import pathlib
import collections
import configparser

from jacquard.storage import open_engine


Config = collections.namedtuple('Config', 'storage')


def load_config(source):
    if hasattr(source, 'read'):
        return _load_config_from_fp(source)
    else:
        with pathlib.Path(source).open('r') as f:
            return _load_config_from_fp(f)


def _load_config_from_fp(f):
    parser = configparser.ConfigParser()
    parser.read_file(f)

    # Construct storage engine
    engine = open_engine(
        parser.get('storage', 'engine'),
        parser.get('storage', 'url', fallback=''),
    )

    return Config(storage=engine)
