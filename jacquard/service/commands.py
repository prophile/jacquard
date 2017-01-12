import werkzeug.debug
import werkzeug.serving

from jacquard.commands import BaseCommand
from jacquard.service import get_wsgi_app


class RunServer(BaseCommand):
    help = "run a (local, debug) server"

    def add_arguments(self, parser):
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
