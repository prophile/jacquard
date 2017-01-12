import pathlib
import threading
import configparser

from jacquard.storage import open_engine


class Config(object):
    def __init__(self, config_file):
        self.storage_engine = config_file.get('storage', 'engine')
        self.storage_url = config_file.get('storage', 'url', fallback='')
        self._thread_local = threading.local()

    @property
    def storage(self):
        if not hasattr(self._thread_local, 'storage'):
            self._thread_local.storage = open_engine(
                self.storage_engine,
                self.storage_url,
            )

        return self._thread_local.storage


def load_config(source):
    if hasattr(source, 'read'):
        return _load_config_from_fp(source)
    else:
        with pathlib.Path(source).open('r') as f:
            return _load_config_from_fp(f)


def _load_config_from_fp(f):
    parser = configparser.ConfigParser()
    parser.read_file(f)

    return Config(parser)
