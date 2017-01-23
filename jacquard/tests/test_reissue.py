import unittest.mock

import pytest

from jacquard.storage.utils import retrying
from jacquard.storage.exceptions import Retry


def test_does_not_reissue_if_successful_exit():
    mock_inner = unittest.mock.Mock()

    @retrying
    def fn():
        mock_inner()

    fn()

    mock_inner.assert_has_calls((unittest.mock.call(),))


def test_reissues_if_retry_is_raised():
    mock_inner = unittest.mock.Mock(side_effect=(Retry(), None))

    @retrying
    def fn():
        mock_inner()

    fn()

    mock_inner.assert_has_calls((unittest.mock.call(), unittest.mock.call()))


def test_does_not_reissue_if_other_exceptions_raised():
    mock_inner = unittest.mock.Mock(side_effect=(ValueError(), None))

    @retrying
    def fn():
        mock_inner()

    with pytest.raises(ValueError):
        fn()


def test_passes_through_args():
    mock_inner = unittest.mock.Mock()

    @retrying
    def fn(arg):
        mock_inner(arg)

    sentinel = object()
    fn(sentinel)
    mock_inner.assert_called_with(sentinel)


def test_passes_through_kwargs():
    mock_inner = unittest.mock.Mock()

    @retrying
    def fn(arg):
        mock_inner(arg)

    sentinel = object()
    fn(arg=sentinel)
    mock_inner.assert_called_with(sentinel)


def test_passes_through_return_values():
    sentinel = object()
    mock_inner = unittest.mock.Mock(return_value=sentinel)

    @retrying
    def fn():
        return mock_inner()

    result = fn()
    assert result is sentinel
