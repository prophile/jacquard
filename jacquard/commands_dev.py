"""Useful commands for Jacquard development."""

import io
import json
import itertools
import contextlib

from werkzeug.test import Client

from jacquard.cli import main as run_command
from jacquard.service import get_wsgi_app
from jacquard.commands import BaseCommand, CommandError
from jacquard.storage.dummy import DummyStore
from jacquard.storage.utils import copy_data


def _shrink(data, is_valid):
    # This is in principle recursive, but we do this with explicit iteration
    # to save on stack space.

    while True:
        if isinstance(data, bool) and data:
            # Try setting bools to false
            return False if is_valid(False) else True
        elif isinstance(data, int) or isinstance(data, float):
            # Try setting numbers to 0, 1 or -1
            if is_valid(0):
                return 0
            elif is_valid(1):
                return 1
            elif is_valid(-1):
                return -1
            else:
                return data
        elif isinstance(data, str):
            if len(data) == 0:
                return data  # as minimal as it gets
            # Try the empty string
            if is_valid(''):
                return ''
            if is_valid(data[1:]):
                data = data[1:]
                continue
            if is_valid(data[:-1]):
                data = data[:-1]
                continue
            return data  # No further string shrinks
        elif isinstance(data, list):
            if len(data) == 0:
                return data  # as minimal as it gets
            # Try the empty list here
            if is_valid([]):
                return []
            # Try dropping the first element
            if is_valid(data[1:]):
                data = data[1:]
                continue
            # Try dropping the last element
            if is_valid(data[:-1]):
                data = data[:-1]
                continue
            # Shrink each element
            any_shrunk = False
            output_elements = []
            for index, element in enumerate(data):
                def is_valid_child(substitution):
                    data_copy = list(data)
                    data_copy[index] = substitution
                    return is_valid(data_copy)
                shrunk_element = _shrink(element, is_valid_child)
                if shrunk_element != element:
                    any_shrunk = True
                output_elements.append(shrunk_element)
            if any_shrunk:
                data = output_elements
                continue
            else:
                return data
        elif isinstance(data, dict):
            if len(data) == 0:
                return data
            # First try the empty dict
            if is_valid({}):
                return {}

            # Drop keys and shrink values
            any_changes = False

            keys = list(data.keys)
            keys.sort()

            for key in keys:
                # See if we can drop this key
                if is_valid({
                    dict_key: dict_value
                    for dict_key, dict_value in data.items()
                    if dict_key != key
                }):
                    del data[key]
                    any_changes = True
                else:
                    # We can't, try to shrink this key
                    def is_valid_substitution(substitution):
                        copied_data = dict(data)
                        copied_data[key] = substitution
                        return is_valid(copied_data)

                    shrunk_value = _shrink(
                        data[key],
                        is_valid_substitution,
                    )

                    if shrunk_value != data[key]:
                        any_changes = True
                        data[key] = shrunk_value

            if not any_changes:
                return data
        else:
            # No shrink on this type
            return data


class Bugpoint(BaseCommand):
    """
    Minimise error by reducing storage.

    Drops keys from storage to minimise the size of test case needed to
    reproduce an exception.
    """

    help = "minimise test case from storage"

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
        log = print

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
            test_client = Client(app)

            def target():
                result = test_client.get(options.url)

                status_class = str(result.status_code)[0]

                if status_class in ('4', '5'):
                    raise ValueError("Class 4 or 5 status")

        def target_failure_mode():
            try:
                target()
            except KeyboardInterrupt:
                # Pass through ^C
                raise
            except Exception as exc:
                return repr(exc)
            else:
                return None

        reference_failure_mode = target_failure_mode()

        if reference_failure_mode is None:
            raise CommandError("Target is not currently failing")

        log("Taking backup of state")
        backup = DummyStore('')
        copy_data(config.storage, backup)

        # Sequence 1: Simplify by dropping keys
        pass_number = itertools.count(1)

        any_changes = True
        log("Dropping keys")
        while any_changes:
            log("Loop {}".format(next(pass_number)))
            any_changes = False

            # Get list of keys
            config.storage.begin_read_only()
            all_keys = list(config.storage.keys())
            config.storage.rollback()
            all_keys.sort()

            for key in all_keys:
                # Try dropping this key and see what happens
                config.storage.begin()
                old_value = config.storage.get(key)
                config.storage.commit({}, (key,))

                failure_mode = target_failure_mode()

                if failure_mode != reference_failure_mode:
                    # This either passes the tests or changes the failure mode,
                    # and so must be kept.
                    config.storage.begin()
                    config.storage.commit({key: old_value}, ())
                else:
                    log("Dropped key {}".format(key))
                    any_changes = True

        # Sequence 1: Simplify by dropping keys
        pass_number = itertools.count(1)

        any_changes = True
        while any_changes:
            log("Loop {}".format(next(pass_number)))
            any_changes = False

            # Get list of keys
            config.storage.begin_read_only()
            all_keys = list(config.storage.keys())
            config.storage.rollback()
            all_keys.sort()

            for key in all_keys:
                # Try dropping this key and see what happens
                config.storage.begin()
                old_value = config.storage.get(key)
                config.storage.commit({}, (key,))

                failure_mode = target_failure_mode()

                if failure_mode != reference_failure_mode:
                    # This either passes the tests or changes the failure mode,
                    # and so must be kept.
                    config.storage.begin()
                    config.storage.commit({key: old_value}, ())
                else:
                    log("Dropped key {}".format(key))
                    any_changes = True

        # Sequence 2: Progressively simplify all remaining keys
        log("Simplifying keys")
        pass_number = itertools.count(1)

        any_changes = True
        while any_changes:
            log("Loop {}".format(next(pass_number)))
            any_changes = False

            # Get list of keys
            config.storage.begin_read_only()
            all_keys = list(config.storage.keys())
            config.storage.rollback()
            all_keys.sort()

            for key in all_keys:
                # Try to shrink this key
                config.storage.begin()
                old_value = config.storage.get(key)
                config.storage.commit({}, (key,))

                def test_validity(new_json):
                    dumped_json = json.dumps(new_json)
                    config.storage.begin()
                    config.storage.commit({key: dumped_json}, ())

                    failure_mode = target_failure_mode()

                    return failure_mode == reference_failure_mode

                parsed_old_value = json.loads(old_value)

                shrunk_value = _shrink(parsed_old_value, test_validity)

                config.storage.begin()
                config.storage.commit({key: json.dumps(shrunk_value)}, ())

                if shrunk_value != parsed_old_value:
                    log("Shrunk key: {}".format(key))
                    any_changes = True

        log("Done bugpointing")

        run_command(["storage-dump"], config)

        log("Restoring state from backup")
        copy_data(backup, config.storage)
