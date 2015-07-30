

import sys
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, Request, build_opener
from urllib import urlencode

import unittest
from occo_test.info_provider_echo import *
from occo.exceptions import KeyNotFoundError, ArgumentError
import json
import subprocess
import time

mgrproc = None

def setup_module(module):
    global mgrproc
    mgrproc = subprocess.Popen(
        ['manager_service','--cfg','occo_test/occo.yaml'])
    # TODO: race condition! This should be some real synchronization
    time.sleep(1)

def teardown_module(*args):
    if mgrproc:
        mgrproc.terminate()

def curl(url, params=None, auth=None, req_type="GET", data=None, headers=None):
    post_req = ["POST", "PUT"]
    get_req = ["GET", "DELETE"]

    if params is not None:
        url += "?" + urlencode(params)

    if req_type not in post_req + get_req:
        raise IOError("Wrong request type {0!r} passed".format(req_type))

    _headers = {}
    handler_chain = []

    if auth is not None:
        manager = HTTPPasswordMgrWithDefaultRealm()
        manager.add_password(None, url, auth["user"], auth["pass"])
        handler_chain.append(HTTPBasicAuthHandler(manager))

    if req_type in post_req and data is not None:
        _headers["Content-Length"] = len(data)

    if headers is not None:
        _headers.update(headers)

    director = build_opener(*handler_chain)

    if req_type in post_req:
        if sys.version_info.major == 3:
            _data = bytes(data, encoding='utf8')
        else:
            _data = bytes(data)

        req = Request(url, headers=_headers, data=_data)
    else:
        req = Request(url, headers=_headers)

    req.get_method = lambda: req_type
    response = director.open(req)

    #return {
    #    "httpcode": response.code,
    #    "headers": response.info(),
    #    "content": response.read()
    #}
    return response.read()

class TestEchoInfoProvider(unittest.TestCase):
    def setUp(self):
        self.provider = InfoProviderEcho()

    def test_provider_directly(self):
        msg = { u'param1' : u'value1' }
        #Test the provider directly with "global.Echo" keyword
        self.assertEqual(self.provider.get("global.Echo", **msg), msg,  
                'global.Echo failed')
        #Test the provider directly against "global.ArgumentError" keyword
        with self.assertRaises(ArgumentError) as context:
            self.provider.get("global.ArgumentError", **msg)
        #Test the provider directly against "global.KeyNotFoundError" keyword
        with self.assertRaises(KeyNotFoundError) as context:
            self.provider.get("global.KeyNotFoundError", **msg)

    def test_echo(self):
        p = { u"param1" : u"value1" }
        result = curl('http://127.0.0.1:5000/info/global.Echo', params=p )
        self.assertEqual({u'result': p}, json.loads(result))
        return

    def test_argumenterror(self):
        #curl 'http://127.0.0.1:5000/info/global.ArgumentError?param1=value1&param2=value2'
        p = { u"param1" : u"value1" }
        result = curl('http://127.0.0.1:5000/info/global.ArgumentError', params=p )
        resultj = json.loads(result)['reason']
        self.assertTrue("Invalid parameter value for key" in resultj)
        return

    def test_keynotfounderror(self):
        #curl 'http://127.0.0.1:5000/info/global.KeyNotFoundError?param1=value1&param2=value2'
        p = { u"param1" : u"value1" }
        result = curl('http://127.0.0.1:5000/info/global.KeyNotFoundError', params=p )
        resultj = json.loads(result)['reason']
        self.assertTrue("Key not found:" in resultj)
        return



