import hashlib
import datetime
import dateutil.tz


FAR_FUTURE = datetime.datetime.max.astimezone(dateutil.tz.tzutc())
DISTANT_PAST = datetime.datetime.min.astimezone(dateutil.tz.tzutc())


def meets_constraints(constraints, user_entry):
    if user_entry is None:
        return constraints.get('anonymous', True)

    if (
        user_entry.join_date >
        constraints.get('joined_before', FAR_FUTURE)
    ):
        return False

    if (
        user_entry.join_date <
        constraints.get('joined_after', DISTANT_PAST)
    ):
        return False

    required_tags = constraints.get('required_tags', ())

    if (
        required_tags and
        any(x not in user_entry.tags for x in required_tags)
    ):
        return False

    excluded_tags = constraints.get('excluded_tags', ())

    if any(x in excluded_tags for x in user_entry.tags):
        return False

    return True


def get_settings(user_id, storage, directory=None):
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
    sha = hashlib.sha256()
    sha.update(("%s::%s" % (experiment_id, user_id)).encode('utf-8'))
    return int.from_bytes(sha.digest(), 'big', signed=False)
