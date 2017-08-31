"""Utility functions for bucket subsystem."""

import random
import hashlib

from jacquard.odm import CREATE, Session

from .models import Bucket
from .constants import NUM_BUCKETS


def user_bucket(user_id):
    """
    Bucket ID for a given user ID.

    Based on a hash of the user ID.
    """
    user_id = str(user_id)

    hasher = hashlib.sha256()
    hasher.update(user_id.encode('utf-8'))

    key = int.from_bytes(hasher.digest(), byteorder='big')

    return key % NUM_BUCKETS


def release(store, name, constraints, branches):
    """
    Release a given configuration.

    This is the main utility for launching experiments. `store` is the storage
    transaction mapping. `name` is a free-form name (generally an experiment
    ID), `constraints` is the constraints covering this release, and `branches`
    is an iterable of (branch ID, num buckets, settings) triples.

    The utility will select buckets which are not already covering the given
    settings, which allows for partial rollout before running a test.
    """
    session = Session(store)

    # Branches is a list of (name, n_buckets, settings) tuples
    all_buckets = [
        session.get(Bucket, x, default=CREATE)
        for x in range(NUM_BUCKETS)
    ]

    edited_settings = set.union(*[set(x[2].keys()) for x in branches])

    valid_bucket_indices = [
        idx
        for idx, bucket in enumerate(all_buckets)
        if is_valid_bucket(bucket, edited_settings, constraints)
    ]

    random.shuffle(valid_bucket_indices)

    for branch_name, n_buckets, settings in branches:
        key = [name, branch_name]
        bucket_indices = valid_bucket_indices[:n_buckets]

        if len(bucket_indices) < n_buckets:
            raise ValueError("Not enough usable buckets")

        valid_bucket_indices = valid_bucket_indices[n_buckets:]

        for bucket_idx in bucket_indices:
            bucket = all_buckets[bucket_idx]

            bucket.add(key, settings, constraints)

    session.flush()


def is_valid_bucket(bucket, new_settings, new_constraints):
    """Is this bucket a valid place for new settings under some constraints."""
    existing = bucket.affected_settings_by_constraints()

    for constraints, settings in existing.items():

        settings_disjoint = frozenset.isdisjoint(settings, new_settings)
        constraints_disjoint = \
            constraints.is_provably_disjoint_from_constraints(new_constraints)

        if not (constraints_disjoint or settings_disjoint):
            return False

    return True


def close(store, name, constraints, branches):
    """
    Close a given configuration.

    This is the main utility for ending experiments. `store` is the storage
    transaction mapping. `name` is a free-form name (generally an experiment
    ID), `constraints` is the constraints covering this release, and `branches`
    is an iterable of (branch ID, num buckets, settings) triples.

    Deliberately looks like `release` and works to counteract its effects.
    """
    session = Session(store)

    keys = [
        [name, x[0]]
        for x in branches
    ]

    for idx in range(NUM_BUCKETS):
        bucket = session.get(Bucket, idx, default=None)
        if bucket is not None:
            for key in keys:
                bucket.remove(key)

    session.flush()
