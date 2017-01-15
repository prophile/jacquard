"""Configuration loading and objects."""

import sys
import pathlib
import threading
import configparser
import collections.abc

from jacquard.storage import open_engine
from jacquard.directory import open_directory


class Config(collections.abc.Mapping):
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
        self.config_file = config_file

        self._load_path()

        self._thread_local = threading.local()

    def _load_path(self):
        for path in self.get('paths', {}).values():
            sys.path.append(path.strip())

    def __getitem__(self, key):
        """Look up config section by name."""
        return self.config_file[key]

    def __len__(self):
        """Total number of config sections."""
        return len(self.config_file)

    def __iter__(self):
        """Iterator over names of config sections."""
        return iter(self.config_file)

    def __contains__(self, key):
        """Existence of config section."""
        return key in self.config_file

    def _thread_local_property(self, name, generator):
        if not hasattr(self._thread_local, name):
            setattr(self._thread_local, name, generator())
        return getattr(self._thread_local, name)

    def _open_storage(self):
        return open_engine(self, self.storage_engine, self.storage_url)

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
            self,
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
