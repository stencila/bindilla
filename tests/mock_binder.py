"""
A mock binder for testing
"""

from tornado import gen
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler


class BuildHandler(RequestHandler):
    """
    Simulate a Stencila Host within the binder

    Get a list of event streams from Binder curing Curl or Httpie like this:
      http --stream https://mybinder.org/build/gh/stencila/images/base-py-binder
    """

    EVENTS = [
        'data: {"phase": "built", "imageName": "gcr.io/binder-prod/r2d-05168b0-stencila-2dimages-0a1ef4:25d8cc48f31c092085e1662144b06f2b63a3de0e", "message": "Found built image, launching...\\n"}',
        'data: {"phase": "launching", "message": "Launching server...\\n"}',
        ':keepalive',
        # Note for this event the URL is replaced with this URL
        'data: {"phase": "ready", "message": "server running at https://hub.mybinder.org/user/stencila-images-mri86aq9/\\n", "url": "http://127.0.0.1:4444/", "token": "sRz1yukLTcapZUL9hEuA6Q"}',
        ''
    ]

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection', 'keep-alive')
        self.set_header('Content-Type', 'text/event-stream')

    @gen.coroutine
    def get(self):
        for event in BuildHandler.EVENTS:
            self.write(event + '\n\n')
            yield self.flush()
            yield gen.sleep(1)


class HostHandler(RequestHandler):
    """
    Simulate a Stencila Host within the binder
    """

    @gen.coroutine
    def get(self):
        yield gen.sleep(1)
        self.write('OK')

    @gen.coroutine
    def post(self):
        yield gen.sleep(1)
        self.write('OK')

    @gen.coroutine
    def put(self):
        yield gen.sleep(1)
        self.write('OK')


if __name__ == "__main__":
    app = Application([
        (r'/build/.*', BuildHandler),
        (r'/stencila-host/.*', HostHandler)
    ])
    server = HTTPServer(app)
    server.listen(4444)
    IOLoop.instance().start()
