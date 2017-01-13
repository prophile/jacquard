"""Command-line utilities for HTTP service subsystem."""

import werkzeug.debug
import werkzeug.serving

from jacquard.commands import BaseCommand
from jacquard.service import get_wsgi_app


class RunServer(BaseCommand):
    """
    Run a debug server.

    **This is for debug, local use only, not production.**

    This command is named to mirror its equivalent in Django. It configures
    the WSGI app and serves it through Werkzeug's simple serving mechanism,
    with a debugger attached, and auto-reloading.
    """

    help = "run a (local, debug) server"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument(
            '-p',
            '--port',
            type=int,
            default=1212,
            help="port to bind to",
        )
        parser.add_argument(
            '-b',
            '--bind',
            type=str,
            default='::1',
            help="address to bind to",
        )

    def handle(self, config, options):
        """Run command."""
        app = get_wsgi_app(config)

        werkzeug.serving.run_simple(
            options.bind,
            options.port,
            app,
            use_reloader=True,
            use_debugger=True,
            use_evalex=True,
            threaded=False,
            processes=1,
        )
