"""Per-user settings lookup."""

from jacquard.buckets import Bucket, user_bucket


def get_settings(user_id, storage, directory=None):
    """
    Look up the current settings dict for a given user ID.

    This takes, in order of preference:

    1. The global defaults,
    2. Any experiment settings for experiments the user is in,
    3. User-specific overrides.
    """
    with storage.transaction(read_only=True) as store:
        defaults = store.get('defaults', {})
        bucket_id = user_bucket(user_id)
        bucket = Bucket.from_json(store.get('buckets/%s' % bucket_id, []))

        if bucket.needs_constraints():
            user_entry = directory.lookup(user_id)
        else:
            user_entry = None

        bucket_settings = bucket.get_settings(user_entry)

        overrides = store.get('overrides/%s' % user_id, {})

    return {**defaults, **bucket_settings, **overrides}
