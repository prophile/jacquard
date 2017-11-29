"""Some general, project-level constants of little use outside Jacquard."""

import os
import pathlib

DEFAULT_CONFIG_FILE_PATH = pathlib.Path(os.environ.get(
    'JACQUARD_CONFIG',
    '/etc/jacquard/config.cfg',
))
