"""
WSGI application target.

This module is designed for use when running the Jacquard server from a WSGI
web server such as waitress or gunicorn. `jacquard.wsgi` would be the module
to target, picking up the WSGI application from `app`.

In this case, the configuration file can be specified through the environment
variable `JACQUARD_CONFIG`; if left unspecified, the file 'config.cfg' in the
current working directory is assumed.
"""

import os
import logging

from jacquard.utils import check_keys
from jacquard.config import load_config
from jacquard.service import get_wsgi_app

from .cli import DEFAULT_CONFIG_FILE_PATH

LOG_LEVEL = os.environ.get('JACQUARD_LOG_LEVEL', 'errors').lower()
KNOWN_LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'errors': logging.ERROR,
}

check_keys((LOG_LEVEL,), KNOWN_LOG_LEVELS, RuntimeError)

logging.basicConfig(level=KNOWN_LOG_LEVELS[LOG_LEVEL])

app = get_wsgi_app(load_config(DEFAULT_CONFIG_FILE_PATH))
