import io
import unittest.mock
import contextlib
import textwrap

from jacquard.cli import main
from jacquard.storage.dummy import DummyStore

def test_smoke_cli_help():
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(['--help'])
    except SystemExit:
        pass

    assert output.getvalue().startswith("usage: ")


def test_help_message_when_given_no_subcommand():
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main([])
    except SystemExit:
        pass

    assert output.getvalue().startswith("usage: ")


def test_run_basic_command():
    config = unittest.mock.Mock()
    config.storage = DummyStore('', data={
        'foo': 'bar',
    })

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        main(['storage-dump'], config=config)

    assert output.getvalue().strip() == textwrap.dedent("""
        foo
        ===
        'bar'

        """
    ).strip()
