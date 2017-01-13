from jacquard.users.settings import FAR_FUTURE, DISTANT_PAST


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