"""Per-user settings lookup."""

import hashlib

from jacquard.experiments.constraints import meets_constraints


def get_settings(user_id, storage, directory=None):
    """
    Look up the current settings dict for a given user ID.

    This takes, in order of preference:

    1. The global defaults,
    2. Any experiment settings for experiments the user is in,
    3. User-specific overrides.
    """
    with storage.transaction() as store:
        defaults = store.get('defaults', {})
        live_experiments = store.get('active-experiments', [])

        experiment_definitions = [
            {**store['experiments/%s' % x], 'id': x}
            for x in live_experiments
        ]
        overrides = store.get('overrides/%s' % user_id, {})

    experiment_settings = {}

    for experiment_def in experiment_definitions:
        constraints = experiment_def.get('constraints', {})

        if constraints:
            if directory is None:
                raise ValueError(
                    "Cannot evaluate constraints on experiment %r "
                    "with no directory" % experiment_def['id'],
                )

            user_entry = directory.lookup(user_id)

            if not meets_constraints(constraints, user_entry):
                continue

        branch = experiment_def['branches'][branch_hash(
            experiment_def['id'],
            user_id,
        ) % len(experiment_def['branches'])]
        experiment_settings.update(branch['settings'])

    return {**defaults, **experiment_settings, **overrides}


def branch_hash(experiment_id, user_id):
    """Get the numeric branch hash for a given experiment ID/user ID pair."""
    sha = hashlib.sha256()
    sha.update(("%s::%s" % (experiment_id, user_id)).encode('utf-8'))
    return int.from_bytes(sha.digest(), 'big', signed=False)
