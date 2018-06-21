## `stencila/bindila`: Binder + Stencila


### FAQ

#### Why is this implemented in Python instead of Node.js, Go, or ...?

BinderHub, and much of the wider Jupyter ecosystem, is implemented in Python. We want to have an implementation that is familiar to that community.

#### Why use Tornado as a server framework instead of Werkzeug, Flask, or ...

For the same reason we are using Python, because BinderHub uses Tornado.

#### Why separate `host` and `host_http_server` files?

The `Host` is implemented in [`bindila/host.py`](bindila/host.py) and a HTTP server is implemented in [`bindila/host_http_server.py`](bindila/host_http_server.py). This is to maintain consistency with the code and file structure in other implementations of the Stencila Host API e.g. [`stencila/py`](https://github.com/stencila/py), [`stencila/node`](https://github.com/stencila/node). Although for Bindila it probably only makes sense to have a HTTP server, in these other implementations there may be more than one server protocol providing access to the host and this structure provides for separation of concerns.

