"""Base for HTTP endpoint plugins."""

import abc
import copy

import werkzeug.routing


class Endpoint(metaclass=abc.ABCMeta):
    """
    Base HTTP endpoint.

    Subclasses must implement `url` and `handle`. `url` is a URL pattern in
    the standard Werkzeug/Flask form, and `handle` is the method which is
    actually called to dispatch the endpoint.

    Instances have two states: bound and unbound. When the endpoint is loaded
    it is instantiated in an unbound state. Before it's actually *dispatched*,
    the dispatcher calls `bind` which copies the endpoint to produce a bound
    version. Bound endpoints have context available in attributes: `reverse`
    and `request`.
    """

    def __init__(self, config):
        """Constructor from system config."""
        self.config = config

    @abc.abstractproperty
    def url(self):
        """
        URL config, to be overridden in subclasses.

        Takes the standard Werkzeug/Flask format. Examples:

        * '/'
        * '/foo/bar/bazz'
        * '/foo/<user>'
        * '/order/<id:int>'

        Full documentation can be found in Werkzeug's `werkzeug.routing` docs.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def handle(self, **kwargs):
        """
        Endpoint handler.

        Any URL parameters are passed in as keyword arguments. This is only
        called on bound instances, so you can rely on `self.request` and
        friends existing.

        Return JSON structures.
        """
        raise NotImplementedError

    def __call__(self, **kwargs):
        """Convenience alias for `handle`."""
        return self.handle(**kwargs)

    @property
    def defaults(self):
        """Default values for URL parameters."""
        return {}

    def build_rule(self, name):
        """Build `Rule` instance which represents this unbound endpoint."""
        return werkzeug.routing.Rule(
            self.url,
            defaults=self.defaults,
            endpoint=self,
        )

    def bind(self, request, reverse):
        """
        Create bound version of this endpoint.

        Clones with `copy.copy` and assigns `instance.request` and
        `instance.reverse`.
        """
        instance = copy.copy(self)
        instance._request = request
        instance._reverse = reverse
        return instance

    @property
    def request(self):
        """Request this endpoint is handling."""
        try:
            return self._request
        except AttributeError:
            raise AttributeError(
                "Unbound endpoint: `request` is only available on bound "
                "endpoints",
            )

    def reverse(self, name, **kwargs):
        """Look up URL for a given endpoint with given kwargs."""
        try:
            reverse = self._reverse
        except AttributeError:
            raise AttributeError(
                "Unbound endpoint: `reverse` is only available on bound "
                "endpoints",
            )
        return reverse(name, **kwargs)
