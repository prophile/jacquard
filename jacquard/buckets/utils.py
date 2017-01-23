import random
import hashlib

from .bucket import Bucket
from .constants import NUM_BUCKETS


def user_bucket(user_id):
    user_id = str(user_id)

    hasher = hashlib.sha256()
    hasher.update(user_id.encode('utf-8'))

    key = int.from_bytes(hasher.digest(), byteorder='big')

    return key % NUM_BUCKETS


def release(store, name, constraints, branches):
    # Branches is a list of (name, n_buckets, settings) tuples
    all_buckets = [
        Bucket.from_json(store.get('buckets/%s' % x, ()))
        for x in range(NUM_BUCKETS)
    ]

    edited_settings = set.union(*[set(x[2].keys()) for x in branches])

    valid_bucket_indices = [
        idx
        for idx, bucket in enumerate(all_buckets)
        if edited_settings.isdisjoint(bucket.affected_settings())
    ]

    random.shuffle(valid_bucket_indices)

    affected_bucket_indices = set()

    for branch_name, n_buckets, settings in branches:
        key = [name, branch_name]
        bucket_indices = valid_bucket_indices[:n_buckets]

        if len(bucket_indices) < n_buckets:
            raise ValueError("Not enough usable buckets")

        valid_bucket_indices = valid_bucket_indices[n_buckets:]

        for bucket_idx in bucket_indices:
            bucket = all_buckets[bucket_idx]
            affected_bucket_indices.add(bucket_idx)

            bucket.add(key, settings, constraints)

    for bucket_idx in affected_bucket_indices:
        store['buckets/%s' % bucket_idx] = all_buckets[bucket_idx].to_json()


def close(store, name, constraints, branches):
    keys = [
        [name, x[0]]
        for x in branches
    ]

    for idx in range(NUM_BUCKETS):
        bucket = Bucket.from_json(store.get('buckets/%s' % idx, ()))
        for key in keys:
            bucket.remove(key)
        new_bucket_json = bucket.to_json()

        if new_bucket_json:
            store['buckets/%s' % idx] = new_bucket_json
        else:
            try:
                del store['buckets/%s' % idx]
            except KeyError:
                pass
