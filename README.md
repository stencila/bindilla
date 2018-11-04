# Bindilla: a Stencila to Binder bridge

[![Build status](https://travis-ci.org/stencila/binder.svg?branch=master)](https://travis-ci.org/stencila/binder)
[![Code coverage](https://codecov.io/gh/stencila/binder/branch/master/graph/badge.svg)](https://codecov.io/gh/stencila/binder)
[![Chat](https://badges.gitter.im/stencila/stencila.svg)](https://gitter.im/stencila/stencila)

A bridge between Stencila and Binder, Bindilla exposes Binder as a Stencila [Host API](https://stencila.github.io/schema/host.html) provider. Using this bridge, clients such as Stencila Desktop or Texture Reader can request, and interact with, execution envionments provided by Binder using the API.


## FAQ

### Why is this implemented in Python instead of Node.js, Go, or ...?

BinderHub, and much of the wider Jupyter ecosystem, is implemented in Python. We want to have an implementation that is familiar to that community.

### Why use Tornado as a server framework instead of Werkzeug, Flask, or ...

For the same reason we are using Python, because BinderHub uses Tornado.

### Why separate `host` and `host_http_server` files?

The `Host` is implemented in [`bindilla/host.py`](bindilla/host.py) and a HTTP server is implemented in [`bindilla/host_http_server.py`](bindilla/host_http_server.py). This is to maintain consistency with the code and file structure in other implementations of the Stencila Host API e.g. [`stencila/py`](https://github.com/stencila/py), [`stencila/node`](https://github.com/stencila/node). Although for Bindilla it probably only makes sense to have a HTTP server, in these other implementations there may be more than one server protocol providing access to the host and this structure provides for separation of concerns.

