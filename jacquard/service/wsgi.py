import json
import werkzeug.routing

from jacquard.users import get_settings


def on_root(config):
    return {'user': '/users/<user>'}


def on_user(config, user):
    settings = get_settings(user, config.storage, config.directory)
    return {**settings, 'user': user}


url_map = werkzeug.routing.Map((
    werkzeug.routing.Rule('/', endpoint=on_root),
    werkzeug.routing.Rule('/users/<user>', endpoint=on_user),
))


def get_wsgi_app(config):
    def application(environ, start_response):
        urls = url_map.bind_to_environ(environ)
        endpoint, kwargs = urls.match()

        response = endpoint(config, **kwargs)

        encoded_response = json.dumps(response).encode('utf-8')
        start_response('200 OK', (
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(encoded_response))),
        ))
        return [encoded_response]
    return application
