import abc
import copy
import werkzeug.routing


class Endpoint(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def url(self):
        pass

    @abc.abstractclassmethod
    def handle(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        return self.handle(**kwargs)

    @property
    def defaults(self):
        return {}

    def build_rule(self, name):
        return werkzeug.routing.Rule(
            self.url,
            defaults=self.defaults,
            endpoint=self,
        )

    def bind(self, config, request, reverse):
        instance = copy.copy(self)
        instance._config = config
        instance._request = request
        instance._reverse = reverse
        return instance

    @property
    def config(self):
        try:
            return self._config
        except AttributeError:
            raise AttributeError(
                "Unbound endpoint: `config` is only available on bound "
                "endpoints",
            )

    @property
    def request(self):
        try:
            return self._request
        except AttributeError:
            raise AttributeError(
                "Unbound endpoint: `request` is only available on bound "
                "endpoints",
            )

    def reverse(self, name, **kwargs):
        try:
            reverse = self.reverse
        except AttributeError:
            raise AttributeError(
                "Unbound endpoint: `reverse` is only available on bound "
                "endpoints",
            )
        return reverse(name, **kwargs)
