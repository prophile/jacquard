"""Command-line utilities for HTTP service subsystem."""

import pathlib

import werkzeug.debug
import werkzeug.serving
import werkzeug.contrib.profiler

from jacquard.service import get_wsgi_app
from jacquard.commands import BaseCommand


class RunServer(BaseCommand):
    """
    Run a debug server.

    **This is for debug, local use only, not production.**

    This command is named to mirror its equivalent in Django. It configures
    the WSGI app and serves it through Werkzeug's simple serving mechanism,
    with a debugger attached, and auto-reloading.
    """

    plumbing = True
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
        parser.add_argument(
            '--profile',
            type=pathlib.Path,
            help="record profiles to the given path",
        )

    def handle(self, config, options):
        """Run command."""
        app = get_wsgi_app(config)

        reload_and_debug = True

        if options.profile is not None:
            options.profile.mkdir(parents=True, exist_ok=True)
            reload_and_debug = False
            app = werkzeug.contrib.profiler.ProfilerMiddleware(
                app=app,
                profile_dir=str(options.profile),
            )

        werkzeug.serving.run_simple(
            options.bind,
            options.port,
            app,
            use_reloader=reload_and_debug,
            use_debugger=reload_and_debug,
            use_evalex=reload_and_debug,
            threaded=False,
            processes=1,
        )
