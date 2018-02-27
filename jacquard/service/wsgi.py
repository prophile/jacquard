"""Main WSGI application."""

import enum
import json
import pprint
import logging
import collections

import yaml
import werkzeug.http
import werkzeug.routing
import werkzeug.wrappers
import werkzeug.exceptions

from jacquard.plugin import plug_all

try:
    # If pygments is installed, add HTML pretty-printing.
    import pygments
    import pygments.lexers
    import pygments.formatters
except ImportError:
    pygments = None


LOGGER = logging.getLogger('jacquard.service.wsgi')


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


@enum.unique
class RepresentationType(enum.Enum):
    """Whether a representation is binary or text-based."""

    BINARY = 'binary'
    TEXT = 'text'


Representation = collections.namedtuple('Representation', (
    'mime_type',
    'type',
    'generate',
))

RepresentationContext = collections.namedtuple('RepresentationContext', (
    'path',
))

REPRESENTATIONS = []


def representation(mime_type, rep_type):
    """Decorator for declaring representations."""
    def wrap(fn):
        REPRESENTATIONS.append(Representation(
            mime_type=mime_type,
            type=rep_type,
            generate=fn,
        ))
        return fn
    return wrap


@representation('application/json', RepresentationType.BINARY)
def generate_json_representation(data, context):
    """
    Represent the given data as JSON.

    Note that the JSON representation is binary. JSON can only be represented
    in UTF-8, UTF-16, or UTF-32 (see RFC 7159), and we stick to UTF-8 here
    unconditionally because:

    * The application/* MIME family doesn't suggest charset negotation will be
      necessary (and some clients can be assumed to probably be checking for
      the exact application/json string),
    * UTF-8 is the 'de facto' standard for JSON,
    * UTF-8 can be detected from the first 4 bytes by RFC 4627 compliant
      clients,
    * UTF-8 avoids endian-ness issues,
    * JSON is mostly going to be unicode-escaping anyway.
    """
    return json.dumps(data).encode('utf-8') + b'\n'


if pygments is not None:
    @representation('text/html', RepresentationType.TEXT)
    def generate_html_representation(data, context):
        """
        Represent the given data in HTML.

        This is the JSON format, but pretty-printed and with syntax
        highlighting due to pygments.
        """
        json_dump = json.dumps(data, indent=2, ensure_ascii=False)
        json_lexer = pygments.lexers.get_lexer_by_name('json')
        html_formatter = pygments.formatters.HtmlFormatter(
            title="Jacquard: {path}".format(
                path=context.path
            ),
            full=True,
        )

        return pygments.highlight(json_dump, json_lexer, html_formatter)


@representation('text/plain', RepresentationType.TEXT)
def generate_plaintext_representation(data, context):
    """
    Represent the given data in plain text.

    This uses Python's built-in pretty formatting. This is not a format
    designed for easy parsing, but that would not be implied by the text/plain
    MIME type anyway. It is, however, generally pretty readable.
    """
    return pprint.pformat(data) + '\n'


@representation('text/x-yaml', RepresentationType.TEXT)
def generate_yaml_text_representation(data, context):
    """
    Represent the given data in textual YAML.

    YAML is not a good interchange format so this is primarily for quick
    hackery purposes.

    Unfortunately YAML does not have a standard MIME type. This textual format
    is for the text/x-yaml MIME type.
    """
    return yaml.safe_dump(data, default_flow_style=False)


@representation('application/x-yaml', RepresentationType.BINARY)
def generate_yaml_binary_representation(data, context):
    """
    Represent the given data in binary YAML.

    YAML is not a good interchange format so this is primarily for quick
    hackery purposes.

    Unfortunately YAML does not have a standard MIME type. This binary format
    is for the application/x-yaml MIME type. It uses UTF-8 for much the same
    reasons as we use UTF-8 for the JSON representation.
    """
    return generate_yaml_text_representation(data, context).encode('utf-8')


def get_wsgi_app(config):
    """Get the main WSGI handler, by config."""
    endpoints = _get_endpoints(config)
    url_map = _get_url_map(endpoints)

    def application(environ, start_response):
        """WSGI callable."""
        try:
            urls = url_map.bind_to_environ(environ)

            LOGGER.debug(
                "%s %s",
                environ['REQUEST_METHOD'],
                environ['PATH_INFO'] or '/',
            )

            def reverse(name, **kwargs):
                endpoint = endpoints[name]
                return urls.build(endpoint, values=kwargs)

            negotiated_content_type = werkzeug.http.parse_accept_header(
                environ.get('HTTP_ACCEPT', '*/*'),
                werkzeug.http.MIMEAccept,
            ).best_match([x.mime_type for x in REPRESENTATIONS])

            if negotiated_content_type is None:
                response_text = b'Cannot satisfy the given MIME type.\n'
                start_response('406 Not Acceptable', [
                    ('Content-Type', 'text/plain; charset=ascii'),
                    ('Content-Length', len(response_text)),
                ])
                return [response_text]

            for selected_representation in REPRESENTATIONS:
                if (
                    selected_representation.mime_type ==
                    negotiated_content_type
                ):
                    break
            else:
                raise AssertionError(
                    "Selected a MIME type without a representation",
                )

            # If the representation is a text representation, we also need to
            # negotiate an encoding.
            if selected_representation.type == RepresentationType.TEXT:
                negotiated_charset = werkzeug.http.parse_accept_header(
                    environ.get('HTTP_ACCEPT_CHARSET', '*'),
                    werkzeug.http.CharsetAccept,
                ).best_match([
                    'utf-8',
                    'utf-16-le',
                    'utf-16-be',
                    'utf-16',
                    'utf-32-le',
                    'utf-32-be',
                    'utf-32',
                    'iso-8859-1',
                    'ascii',
                ])

                if negotiated_charset is None:
                    response_text = b'Cannot satisfy the given charsets.\n'
                    start_response('406 Not Acceptable', [
                        ('Content-Type', 'text/plain; charset=ascii'),
                        ('Content-Length', len(response_text)),
                    ])
                    return [response_text]

            request = werkzeug.wrappers.Request(environ)

            endpoint, kwargs = urls.match()

            endpoint = endpoint.bind(
                reverse=reverse,
                request=request,
            )

            response = endpoint.handle(**kwargs)

            representation_context = RepresentationContext(
                path=request.path,
            )
            represented_response = selected_representation.generate(
                response,
                representation_context,
            )

            if selected_representation.type == RepresentationType.TEXT:
                # If this is a text-based representation we also need to
                # encode it.
                try:
                    encoded_response = represented_response.encode(
                        negotiated_charset,
                    )
                except UnicodeEncodeError:
                    response_text = b'This charset cannot encode the data.\n'
                    start_response('406 Not Acceptable', [
                        ('Content-Type', 'text/plain; charset=ascii'),
                        ('Content-Length', len(response_text)),
                    ])
                    return [response_text]
                content_type = '{mime}; charset={charset}'.format(
                    mime=selected_representation.mime_type,
                    charset=negotiated_charset,
                )
            else:
                # For binary representations we just return directly.
                encoded_response = represented_response
                content_type = selected_representation.mime_type

            start_response('200 OK', [
                ('Content-Type', content_type),
                ('Content-Length', str(len(encoded_response))),
            ])
            # Don't send the body for a HEAD request
            if request.method == 'HEAD':
                return []
            return [encoded_response]
        except werkzeug.exceptions.HTTPException as e:
            return e(environ, start_response)
    return application
