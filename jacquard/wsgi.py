import os

from jacquard.service import get_wsgi_app
from jacquard.config import load_config

app = get_wsgi_app(
    load_config(
        os.environ.get('JACQUARD_CONFIG', 'config.cfg'),
    ),
)
