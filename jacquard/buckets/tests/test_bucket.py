import pytest

from jacquard.odm import Session
from jacquard.buckets import Bucket
from jacquard.constraints import Constraints
from jacquard.buckets.utils import release
from jacquard.buckets.constants import NUM_BUCKETS
from jacquard.buckets.exceptions import NotEnoughBucketsException


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


def test_can_get_empty_bucket_from_old_format():
    session = Session({'buckets/1': []})
    bucket = session.get(Bucket, 1)
    # Force bucket to a string in order to reify the fields. This validates
    # that the fields are accessible.
    str(bucket)


def test_conflict_on_release():
    store = {}
    release(
        store=store,
        name='foo',
        constraints=Constraints(),
        branches=[
            ('foo-branch', NUM_BUCKETS // 2, {'setting': 'value'}),
        ],
    )
    release(
        store=store,
        name='bar',
        constraints=Constraints(),
        branches=[
            ('bar-branch', NUM_BUCKETS // 2, {'setting': 'value2'}),
        ],
    )

    with pytest.raises(NotEnoughBucketsException) as e:
        release(
            store=store,
            name='bazz',
            constraints=Constraints(),
            branches=[
                ('bar-branch', NUM_BUCKETS // 2, {'setting': 'value2'}),
            ],
        )

    assert e.value.conflicts == {'foo', 'bar'}
