"""Main WSGI application."""

import json

import werkzeug.routing
import werkzeug.wrappers
import werkzeug.exceptions

from jacquard.plugin import plug_all


def _get_endpoints(config):
    return {
        name: cls()(config)
        for name, cls in plug_all('http_endpoints')
    }


def _get_url_map(endpoints):
    urls = [
        endpoint.build_rule(name)
        for name, endpoint in endpoints.items()
    ]
    return werkzeug.routing.Map(urls)


def get_wsgi_app(config):
    """Get the main WSGI handler, by config."""
    endpoints = _get_endpoints(config)
    url_map = _get_url_map(endpoints)

    def application(environ, start_response):
        """WSGI callable."""
        try:
            urls = url_map.bind_to_environ(environ)

            def reverse(name, **kwargs):
                print(endpoints.keys())
                endpoint = endpoints[name]
                return urls.build(endpoint, values=kwargs)

            request = werkzeug.wrappers.Request(environ)

            endpoint, kwargs = urls.match()

            endpoint = endpoint.bind(
                reverse=reverse,
                request=request,
            )

            response = endpoint.handle(**kwargs)

            encoded_response = (json.dumps(response) + '\n').encode('utf-8')
            start_response('200 OK', [
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(encoded_response))),
            ])
            return [encoded_response]
        except werkzeug.exceptions.HTTPException as e:
            return e(environ, start_response)
    return application
