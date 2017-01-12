import pathlib
import threading
import configparser

from jacquard.storage import open_engine


class Config(object):
    def __init__(self, config_file):
        self.storage_engine = config_file.get('storage', 'engine')
        self.storage_url = config_file.get('storage', 'url', fallback='')
        self._thread_local = threading.local()

    def _thread_local_property(self, name, generator):
        if not hasattr(self._thread_local, name):
            setattr(self._thread_local, name, generator())
        return getattr(self._thread_local, name)

    def _open_storage(self):
        return open_engine(self.storage_engine, self.storage_url)

    @property
    def storage(self):
        return self._thread_local_property('storage', self._open_storage)


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
