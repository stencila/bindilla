# Bindilla: a Stencila to Binder bridge

[![Build status](https://travis-ci.org/stencila/bindilla.svg?branch=master)](https://travis-ci.org/stencila/bindilla)
[![Code coverage](https://codecov.io/gh/stencila/bindilla/branch/master/graph/badge.svg)](https://codecov.io/gh/stencila/bindilla)
[![Chat](https://badges.gitter.im/stencila/stencila.svg)](https://gitter.im/stencila/stencila)

## What?

Bindilla acts as a bridge between [Stencila](https://stenci.la) and [Binder](https://mybinder.org/). Using this bridge, clients such as Stencila Desktop or RDS Reader can request, and interact with, alternative execution envionments provided by Binder.

## Why?

Stencila clients talk to execution contexts using an [API](https://stencila.github.io/schema/host.html). This API is implemented by several packages including [stencila/py](https://github.com/stencila/py), [stencila/r](https://github.com/stencila/r), and [stencila/node](https://github.com/stencila/node). These packages are available within a Binder container via [nbstencilaproxy](https://github.com/minrk/nbstencilaproxy). You can embed a reproducible document into the container and launch it via a per-user Binder container.

However, in some cases you don't want to rely on having a running container to deliver your reproducible document for each reader. Instead, you can use a [progressive enhancement approach to reproducibility](https://elifesciences.org/labs/e5737fd5/designing-progressive-enhancement-into-the-academic-manuscript) so that reproducible elements can be made dynamic, on demand, based on user interaction. The API is designed to allow for this use case, allowing user interfaces to connect to alternative execution contexts both local and remote. By exposing the API as a bridge Bindilla enables this use case for execution contexts hosted on Binder.

## FAQ

### Why is this implemented in Python instead of Node.js, Go, or ...?

BinderHub, and much of the wider Jupyter ecosystem, is implemented in Python. We want to have an implementation that is familiar to that community.

### Why use Tornado as a server framework instead of Werkzeug, Flask, or ...

For the same reason we are using Python, because BinderHub uses Tornado.

### Why separate `host` and `host_http_server` files?

The `Host` is implemented in [`bindilla/host.py`](bindilla/host.py) and a HTTP server is implemented in [`bindilla/host_http_server.py`](bindilla/host_http_server.py). This is to maintain consistency with the code and file structure in other implementations of the Stencila Host API e.g. [`stencila/py`](https://github.com/stencila/py), [`stencila/node`](https://github.com/stencila/node). Although for Bindilla it probably only makes sense to have a HTTP server, in these other implementations there may be more than one server protocol providing access to the host and this structure provides for separation of concerns.

