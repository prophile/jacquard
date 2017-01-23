import pytest

from jacquard.buckets.constants import NUM_BUCKETS


@pytest.mark.parametrize('divisor', (
    2,
    3,
    4,
    5,
    6,
    10,
    100,
))
def test_divisible(divisor):
    assert NUM_BUCKETS % divisor == 0


def test_at_least_three_buckets_per_percent():
    assert NUM_BUCKETS / 100 >= 3
