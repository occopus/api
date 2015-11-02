### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.

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
