"""Configuration loading and objects."""

import pathlib
import threading
import configparser

from jacquard.storage import open_engine
from jacquard.directory import open_directory


class Config(object):
    """
    System configuration.

    Users should not instantiate this class directly but instead use the
    public `load_config` function.
    """

    def __init__(self, config_file):
        """Internal constructor."""
        self.storage_engine = config_file.get('storage', 'engine')
        self.storage_url = config_file.get('storage', 'url', fallback='')
        self.directory_settings = config_file['directory']

        self._thread_local = threading.local()

    def _thread_local_property(self, name, generator):
        if not hasattr(self._thread_local, name):
            setattr(self._thread_local, name, generator())
        return getattr(self._thread_local, name)

    def _open_storage(self):
        return open_engine(self.storage_engine, self.storage_url)

    @property
    def storage(self):
        """
        Key-value storage engine.

        Note that this is actually thread-local, so users need not worry
        about thread synchronisation of connections.
        """
        return self._thread_local_property('storage', self._open_storage)

    def _open_directory(self):
        kwargs = {
            key: value
            for key, value in self.directory_settings.items()
            if key != 'engine'
        }
        return open_directory(
            self.directory_settings['engine'],
            kwargs,
        )

    @property
    def directory(self):
        """
        User lookup directory.

        Note that this is actually thread-local, so users need not worry
        about thread synchronisation of connections.
        """
        return self._thread_local_property('directory', self._open_directory)


def load_config(source):
    """
    Load `Config` from file.

    `source` may be given either as a file-like or path-like object. In the
    former case it should be opened for reading in text/unicode mode.
    """
    if hasattr(source, 'read'):
        return _load_config_from_fp(source)
    else:
        with pathlib.Path(source).open('r') as f:
            return _load_config_from_fp(f)


def _load_config_from_fp(f):
    parser = configparser.ConfigParser()
    parser.read_file(f)

    return Config(parser)
