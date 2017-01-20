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
        instance.config = config
        instance.request = request
        instance.reverse = reverse
        return instance
