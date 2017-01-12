import json
import werkzeug.routing
import werkzeug.exceptions

from jacquard.users import get_settings
from jacquard.users.settings import meets_constraints, branch_hash


def on_root(config):
    return {'user': '/users/<user>', 'experiments': '/experiment'}


def on_user(config, user):
    settings = get_settings(user, config.storage, config.directory)
    return {**settings, 'user': user}


def on_experiments(config):
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
            'state': 'active' if experiment['id'] in active_experiments else 'inactive',
            'name': experiment.get('name', experiment['id']),
        }
        for experiment in experiments
    ]


def on_experiment(config, experiment):
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
    def application(environ, start_response):
        try:
            urls = url_map.bind_to_environ(environ)
            endpoint, kwargs = urls.match()

            response = endpoint(config, **kwargs)

            encoded_response = json.dumps(response).encode('utf-8')
            start_response('200 OK', (
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(encoded_response))),
            ))
            return [encoded_response]
        except werkzeug.exceptions.HTTPException as e:
            return e(environ, start_response)
    return application
