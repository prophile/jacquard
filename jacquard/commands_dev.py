"""Useful commands for Jacquard development."""

import io
import json
import functools
import itertools
import contextlib

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from jacquard.cli import main as run_command
from jacquard.service import get_wsgi_app
from jacquard.storage import DummyStore, copy_data
from jacquard.commands import BaseCommand, CommandError
from jacquard.utils_dev import shrink


class _DuplicateStorageConfig(object):
    """Dummy config emulator with a duplicate store."""

    def __init__(self, config):
        """
        Init from config.

        Copies the storage but otherwise passes through.
        """
        self.storage = DummyStore('')
        print("Copying all data to a local version")
        copy_data(config.storage, self.storage)
        self.config = config

    def __getattr__(self, item):
        """Attribute lookup pass-through."""
        return getattr(self.config, item)


class Bugpoint(BaseCommand):
    """
    Minimise error by reducing storage.

    Drops keys from storage to minimise the size of test case needed to
    reproduce an exception.
    """

    help = "minimise test case from storage"

    plumbing = True

    def add_arguments(self, parser):
        """Add command-line arguments."""
        target = parser.add_mutually_exclusive_group(required=True)

        target.add_argument(
            '--command',
            type=str,
            help="command to run",
            nargs='*',
        )
        target.add_argument(
            '--url',
            type=str,
            help="url to fetch",
        )

    def handle(self, config, options):
        """Run command."""
        replacement_config = _DuplicateStorageConfig(config)

        target = self._get_run_target(replacement_config, options)
        target_failure_mode = functools.partial(
            self._failure_mode,
            target,
        )

        reference_failure_mode = target_failure_mode()

        if reference_failure_mode is None:
            raise CommandError("Target is not currently failing")

        print("Failure mode: ", reference_failure_mode)

        with self._backed_up_storage(replacement_config.storage):
            def predicate():
                """Determine if the config maintains the original failure."""
                return target_failure_mode() == reference_failure_mode

            # Sequence 1: Simplify by dropping keys
            print("Dropping keys")
            self._progressively_simplify(
                replacement_config.storage,
                self._try_dropping_key,
                predicate,
            )

            # Sequence 2: Progressively simplify all remaining keys

            print("Simplifying keys")
            self._progressively_simplify(
                replacement_config.storage,
                self._try_simplifying_key,
                predicate,
            )

            print("Done bugpointing")

            # Output storage state
            run_command(["storage-dump"], replacement_config)

    def _failure_mode(self, target):
        """
        Get a representation of the failure mode of a run target.

        The nature of this representation is unspecified other than that:

         * In case of no exception, it is None;
         * In case of an exception it is printable;
         * In all cases it has functional equality.

        In order to make life easier if bugpoint is feeling particularly slow,
        we special-case KeyboardInterrupt and pass it straight through.
        """
        try:
            target()
        except KeyboardInterrupt:
            # Pass through ^C
            raise
        except Exception as exc:
            return repr(exc)
        else:
            return None

    def _progressively_simplify(self, storage, process, predicate):
        """
        Repeatedly simplify storage, using `process`.

        Process is a callable taking a storage engine and a key, and returning
        whether it committed any changes or not. The `predicate` is an argument
        to `process`, determining whether a simplification has been valid.
        """
        pass_number = itertools.count(1)

        any_changes = True
        while any_changes:
            print("Pass {number}".format(number=next(pass_number)))
            any_changes = False

            # Get list of keys
            storage.begin_read_only()
            all_keys = list(storage.keys())
            storage.rollback()
            all_keys.sort()

            for key in all_keys:
                any_changes = process(storage, key, predicate) or any_changes

    def _try_dropping_key(self, storage, key, predicate):
        storage.begin()
        old_value = storage.get(key)
        storage.commit({}, (key,))

        if not predicate():
            # This either passes the tests or changes the failure mode,
            # and so must be kept.
            storage.begin()
            storage.commit({key: old_value}, ())
            return False
        else:
            print("Dropped key {key}".format(key=key))
            return True

    def _try_simplifying_key(self, storage, key, predicate):
        storage.begin()
        old_value = storage.get(key)
        storage.commit({}, (key,))

        def test_validity(new_json):
            dumped_json = json.dumps(new_json)
            storage.begin()
            storage.commit({key: dumped_json}, ())

            return predicate()

        parsed_old_value = json.loads(old_value)

        shrunk_value = shrink(parsed_old_value, test_validity)

        storage.begin()
        storage.commit({key: json.dumps(shrunk_value)}, ())

        if shrunk_value != parsed_old_value:
            print("Shrunk key: {key}".format(key=key))
            return True
        else:
            return False

    def _get_run_target(self, config, options):
        """
        Get the 'run target' out from options.

        This is a nullary callable which is expected to raise an exception -
        the exception we are needing to debug.

        For the command case it's a wrapped version of the command, which
        silences stdout and stderr.

        For the URL case it's a call with a WSGI client which catches 4xx and
        5xx status codes turning them into ValueErrors.
        """
        if options.command:
            def target():
                out_stream = io.StringIO()

                with contextlib.ExitStack() as context:
                    context.enter_context(
                        contextlib.redirect_stdout(out_stream),
                    )
                    context.enter_context(
                        contextlib.redirect_stderr(out_stream),
                    )

                    run_command(options.command, config)
        elif options.url:
            app = get_wsgi_app(config)
            test_client = Client(app, BaseResponse)

            def target():
                result = test_client.get(options.url)

                status_class = str(result.status_code)[0]

                if status_class in ('4', '5'):
                    raise ValueError("Status: {code}".format(
                        code=result.status_code,
                    ))
        else:
            raise AssertionError("No target type")

        return target

    @contextlib.contextmanager
    def _backed_up_storage(self, storage):
        """
        Back up storage and restore it on exiting.

        A convenience context manager.
        """
        backup = DummyStore('')
        copy_data(storage, backup)

        try:
            yield
        finally:
            copy_data(backup, storage)
