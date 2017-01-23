import hashlib

from .constants import NUM_BUCKETS


def user_bucket(user_id):
    user_id = str(user_id)

    hasher = hashlib.sha256()
    hasher.update(user_id.encode('utf-8'))

    key = int.from_bytes(hasher.digest(), byteorder='big')

    return key % NUM_BUCKETS
