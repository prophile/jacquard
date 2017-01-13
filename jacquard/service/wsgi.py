"""Main WSGI application."""

import json
import werkzeug.routing
import werkzeug.exceptions

from jacquard.users import get_settings
from jacquard.users.settings import branch_hash
from jacquard.experiments.constraints import meets_constraints


def on_root(config):
    """
    The / endpoint.

    Returns a small number of URLs to the rest of the system. Probably not
    hugely useful for production, provided primarily to make the API more
    discoverable without probing into the source.

    If you're here probing into the source anyway, this goal has evidently
    failed. Please accept my apologies.
    """
    return {'user': '/users/<user>', 'experiments': '/experiment'}


def on_user(config, user):
    """
    The settings-for-user endpoint.

    This is the primary endpoint for normal interactive use. It just looks up
    the current settings for a given user ID and returns them.
    """
    settings = get_settings(user, config.storage, config.directory)
    return {**settings, 'user': user}


def on_experiments(config):
    """
    The experiments index endpoint.

    This is for use in reporting tooling: it provides a brief summary of all
    experiments known to the system, as well as whether or not they are
    active.
    """
    with config.storage.transaction() as store:
        active_experiments = store.get('active-experiments', ())
        experiments = []

        for key in store:
            if not key.startswith('experiments/'):
                continue
            definition = store[key]
            experiments.append(definition)

    return [
        {
            'id': experiment['id'],
            'url': '/experiment/%s' % experiment['id'],
            'state':
                'active'
                if experiment['id'] in active_experiments
                else 'inactive',
            'name': experiment.get('name', experiment['id']),
        }
        for experiment in experiments
    ]


def on_experiment(config, experiment):
    """
    The experiment lookup endpoint.

    This provides detailed data on a specific experiment, including lists
    of all user IDs in each of its branches.

    As a result this is quite expensive to hit.

    Provided for reporting tooling which runs statistics.
    """
    with config.storage.transaction() as store:
        experiment_config = store['experiments/%s' % experiment]

    branch_ids = [branch['id'] for branch in experiment_config['branches']]
    branches = {x: [] for x in branch_ids}

    constraints = experiment_config.get('constraints', {})

    for user_entry in config.directory.all_users():
        if not meets_constraints(constraints, user_entry):
            continue

        branch_id = branch_ids[
            branch_hash(experiment, user_entry.id) %
            len(branch_ids)
        ]

        branches[branch_id].append(user_entry.id)

    return {
        'id': experiment_config['id'],
        'name': experiment_config.get('name', experiment_config['id']),
        'launched': experiment_config.get('launched'),
        'concluded': experiment_config.get('concluded'),
        'branches': branches,
    }


url_map = werkzeug.routing.Map((
    werkzeug.routing.Rule('/', endpoint=on_root),
    werkzeug.routing.Rule('/users/<user>', endpoint=on_user),
    werkzeug.routing.Rule('/experiment', endpoint=on_experiments),
    werkzeug.routing.Rule('/experiment/<experiment>', endpoint=on_experiment),
))


def get_wsgi_app(config):
    """Get the main WSGI handler, by config."""
    def application(environ, start_response):
        """WSGI callable."""
        try:
            urls = url_map.bind_to_environ(environ)
            endpoint, kwargs = urls.match()

            response = endpoint(config, **kwargs)

            encoded_response = json.dumps(response).encode('utf-8')
            start_response('200 OK', [
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(encoded_response))),
            ])
            return [encoded_response]
        except werkzeug.exceptions.HTTPException as e:
            return e(environ, start_response)
    return application
