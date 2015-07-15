
import unittest
import occo.infobroker as ib

__all__ = ['InfoProviderEcho']

@ib.provider
class InfoProviderEcho(ib.InfoProvider):
    @ib.provides("global.Echo")
    def echo(self, *args, **kwargs):
        return kwargs

    @ib.provides("global.ArgumentError")
    def argumenterror(self, **kwargs):
        raise ib.ArgumentError(kwargs)

    @ib.provides("global.KeyNotFoundError")
    def keynotfounderror(self, **kwargs):
        raise ib.KeyNotFoundError(kwargs)
