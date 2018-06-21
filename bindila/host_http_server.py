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

    def options(self):
        self.set_status(204)
        self.finish()

    def respond(self, value):
        body = json.dumps(value, indent=2)
        self.write(body)


class IndexHandler(BaseHandler):

    def get(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/html')
        return self.write('<p>Hello, this is Bindila. See the docs.</p>')


class ManifestHandler(BaseHandler):

    def get(self, environs):
        self.respond(
            HOST.manifest(environs.split(',') if environs else None)
        )


class EnvironHandler(BaseHandler):

    def post(self, environ_or_id):
        self.respond(
            HOST.launch_environ(environ_or_id)
        )

    def get(self, environ_or_id):
        self.respond(
            HOST.inspect_environ(environ_or_id)
        )


class ProxyHandler(BaseHandler):

    def get(self, idd, path):
        self.respond(
            HOST.proxy_binder(idd, path)
        )


def make():
    v1_app = Application([
        (r'^/?(?P<environs>.*?)/v1/manifest/?', ManifestHandler),
        (r'^.*?/v1/environs/(?P<environ_or_id>.+)', EnvironHandler),
        (r'^.*?/v1/proxy/.+', ProxyHandler)
    ])

    v0_app = Application([
        (r'^/?(?P<environs>.*?)/v0/manifest/?', ManifestHandler),
        (r'^.*?/v0/environ/(?P<environ_or_id>.+)', EnvironHandler),
        (r'^.*?/v0/proxy/(?P<idd>[^\/]+)/?(?P<path>.+)', ProxyHandler)
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
