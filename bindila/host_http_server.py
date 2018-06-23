"""
Module for serving the ``Host`` API via HTTP
"""

import json

import tornado
from tornado.ioloop import IOLoop
from tornado.routing import Rule, RuleRouter, PathMatches
from tornado.httpserver import HTTPServer
from tornado.web import Application, RequestHandler

from .host import HOST


class BaseHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Server', 'Bindila / Tornado %s' % tornado.version)
        self.set_header('Content-Type', 'application/json')

        # Use origin of request to avoid browser errors like
        # "The value of the 'Access-Control-Allow-Origin' header in the
        # response must not be the wildcard '*' when the
        # request's credentials mode is 'include'."
        origin = self.request.headers.get('Origin', '')
        self.set_header('Access-Control-Allow-Origin', origin)
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        self.set_header('Access-Control-Max-Age', '86400')

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def send(self, value):
        body = json.dumps(value, indent=2)
        self.write(body)


class IndexHandler(BaseHandler):

    def get(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/html')
        return self.write('<p>Hello, this is Bindila. See the docs.</p>')


class ManifestHandler(BaseHandler):

    def get(self, environs):
        self.send(HOST.manifest(environs.split(',') if environs else None))


class EnvironHandler(BaseHandler):

    async def post(self, environ_or_id):
        self.send(await HOST.launch_environ(environ_or_id))

    def get(self, idd):
        self.send(HOST.inspect_environ(idd))


class ProxyHandler(BaseHandler):

    async def get(self, idd, path):
        self.write(await HOST.proxy_environ('GET', idd, path))

    async def post(self, idd, path):
        self.write(await HOST.proxy_environ('POST', idd, path, self.request.body))

    async def put(self, idd, path):
        self.write(await HOST.proxy_environ('PUT', idd, path, self.request.body))


def make():
    v1_app = Application([
        (r'^/?(?P<environs>.*?)/v1/manifest/?', ManifestHandler),
        (r'^.*?/v1/environs/(?P<environ_or_id>.+)', EnvironHandler),
        (r'^.*?/v1/proxy/(?P<idd>[^\/]+)/(?P<path>.+)', ProxyHandler)
    ])

    v0_app = Application([
        (r'^/?(?P<environs>.*?)/v0/manifest/?', ManifestHandler),
        (r'^.*?/v0/environ/(?P<environ_or_id>.+)', EnvironHandler),
        (r'^.*?/v0/proxy/(?P<idd>[^\/]+)/(?P<path>.+)', ProxyHandler)
    ])

    index_app = Application([
        (r'^/', IndexHandler)
    ])

    return RuleRouter([
        Rule(PathMatches(r'^.*?/v1/.*'), v1_app),
        Rule(PathMatches(r'^.*?/v0/.*'), v0_app),
        Rule(PathMatches(r'^/'), index_app)
    ])


def run():
    router = make()
    server = HTTPServer(router)
    server.listen(8888)
    IOLoop.current().start()
