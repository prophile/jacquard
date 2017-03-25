import io
import os
import shlex
import pathlib
import datetime
import textwrap
import contextlib
import unittest.mock

import yaml
import pytest
import dateutil.tz
import werkzeug.test

from jacquard.cli import main
from jacquard.config import load_config
from jacquard.service import get_wsgi_app
from jacquard.directory.base import UserEntry
from jacquard.directory.dummy import DummyDirectory

JACQUARD_ROOT = pathlib.Path(__file__).parent.parent.parent
INTEGRATION_TESTS_ROOT = JACQUARD_ROOT / 'integration-tests'


TEST_CONFIG = """
[storage]
engine = dummy
url = about:blank

[directory]
engine = dummy
"""


_INTEGRATION_TEST_FILES = [
    x.name
    for x in INTEGRATION_TESTS_ROOT.glob('*.yaml')
]


if not _INTEGRATION_TEST_FILES:
    raise AssertionError(
        "Found no integration tests, at root %s" %
        INTEGRATION_TESTS_ROOT.absolute(),
    )


@contextlib.contextmanager
def _temporary_working_directory(pwd):
    new_pwd = str(pwd)
    old_pwd = os.getcwd()
    os.chdir(new_pwd)
    try:
        yield
    finally:
        os.chdir(old_pwd)


@pytest.mark.parametrize('test_file', [
    x.name
    for x in INTEGRATION_TESTS_ROOT.glob('*.yaml')
])
def test_integration(test_file):
    with (INTEGRATION_TESTS_ROOT / test_file).open('r') as f:
        test_config = yaml.safe_load(f)

    config = load_config(io.StringIO(TEST_CONFIG))
    config = unittest.mock.Mock(wraps=config)
    config.directory = DummyDirectory(users=(
        UserEntry(id='1', join_date=datetime.datetime(
            2017, 1, 1,
            tzinfo=dateutil.tz.tzutc(),
        ), tags=()),
        UserEntry(id='2', join_date=datetime.datetime(
            2017, 1, 2,
            tzinfo=dateutil.tz.tzutc(),
        ), tags=('tag1', 'tag2'))
    ))

    wsgi = get_wsgi_app(config)
    test_client = werkzeug.test.Client(wsgi)

    for step in test_config:
        if 'command' in step:
            stdout = io.StringIO()

            args = shlex.split(step['command'])

            try:
                with contextlib.redirect_stdout(stdout):
                    with _temporary_working_directory(JACQUARD_ROOT):
                        main(args, config=config)
            except SystemExit:
                pass

            output = stdout.getvalue()

        elif 'get' in step:
            path = step['get']

            data, status, headers = test_client.get(path)

            assert status == '200 OK'

            output = b''.join(data).decode('utf-8')

        if 'expect' in step:
            expected_output = textwrap.dedent(step['expect']).strip()
            actual_output = textwrap.dedent(output).strip()

            assert expected_output == actual_output

        if 'expect_yaml' in step:
            expected_output = step['expect_yaml']
            actual_output = yaml.safe_load(output)

            assert expected_output == actual_output
