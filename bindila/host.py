"""
Module for defining a Stencila ``Host``
"""

import datetime
import json
import re
import uuid

import pytz
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from .environs import ENVIRONS


class Host:
    """
    A Stencila ``Host``
    """

    def __init__(self):
        # A list of environs available in manifest
        # Initialized with a list of defaults
        self._environs = [self.parse_environ(environ) for environ in ENVIRONS]

        self._binder_host = 'https://mybinder.org'
        #self._binder_host = 'http://localhost:4444'

        # A list of binders that have been launched by
        # this Bindila instance
        self._binders = {}

        self.http_client = AsyncHTTPClient()

    def manifest(self, extra_environs=None):
        environs = self._environs
        if extra_environs:
            environs = [self.parse_environ(environ) for environ in extra_environs] + self._environs
        return {
            'stencila': {
                'package': 'bindila'
            },
            'environs': environs,
            # Properties expected by the client
            'types': [],  # v0 API
            'services': []  # v1 API
        }

    @staticmethod
    def parse_environ(binder_path):
        """
        Parse a Binder path into an environment spec

        Binder repo paths have the pattern
        ```<provider-name>/<org-name>/<repo-name>/<branch|commit|tag>``
        The ``<branch|commit|tag>`` part is optional and defaults to ``master``
        """
        parts = binder_path.split('/')
        provider = parts[0]
        org = parts[1]
        repo = parts[2]
        ref = parts[3] if len(parts) == 4 else 'master'
        name = '{}/{}/{}'.format(provider, org, repo)
        idd = 'binder://{}/{}'.format(name, ref)
        return {
            # Properties required by Host API
            'id': idd,
            'name': name,
            'version': ref,
            # Additional properties used to
            # construct the Binder launch URL
            'provider': provider,
            'org': org,
            'repo': repo
        }

    async def launch_environ(self, environ_id):
        """
        Launch an environment
        """

        # Parse the environ string into an environ spec
        binder_path = re.match(r'^binder:\/\/(.+)', environ_id).group(1)
        environ = self.parse_environ(binder_path)

        # Generate a unique id for the binder
        binder_id = uuid.uuid4().hex

        # Record the binder's details so that we can record
        # events associated with it and retrieve them using `inspect`
        binder = {
            'id': binder_id,
            'environ': environ,
            'phase': None,
            'events': []
        }

        # Build the binder URL from the environ
        environ = binder['environ']
        url = self._binder_host + '/build/%(provider)s/%(org)s/%(repo)s/%(version)s' % environ

        # Ask mybinder.org to launch the binder
        binder['request'] = {
            'time': datetime.datetime.now(tz=pytz.UTC).isoformat(),
            'url': url
        }

        def handle_stream(event):
            event = event.decode()
            print(event)
            if ":" in event:
                (field, value) = event.split(":", 1)
                field = field.strip()
                if field == 'data':
                    data = json.loads(value)
                    data['time'] = datetime.datetime.now(tz=pytz.UTC).isoformat()
                    binder['events'].append(data)
                    binder['phase'] = data.get('phase')
                    binder['base_url'] = data.get('url')
                    binder['token'] = data.get('token')

        request = HTTPRequest(
            url=url,
            method='GET',
            headers={'content-type': 'text/event-stream'},
            request_timeout=0,
            streaming_callback=handle_stream
        )
        await self.http_client.fetch(request)

        if 0:
            # Return a local path the client can use to connect
            # to the binder
            binder['path'] = '/proxy/' + binder_id
        else:
            if binder.get('base_url'):
                binder['url'] = binder['base_url'] + 'stencila-host'

        self._binders[binder_id] = binder

        return binder

    def inspect_environ(self, binder_id):
        return self._binders.get(binder_id)

    async def proxy_environ(self, method, binder_id, path, body=None):
        """
        Proxy requests through to the binder

        Need to provide token and append `stencila-host` to URL
        e.g https://hub.mybinder.org/user/stencila-images-mukdlnm5/stencila-host
        """
        binder = self._binders.get(binder_id)
        if not binder:
            raise RuntimeError('No such binder: {}'.format(binder_id))

        if binder['phase'] != 'ready':
            return None

        url = binder['base_url'] + 'stencila-host/' + path
        request = HTTPRequest(
            url=url,
            method=method,
            headers={
                'Authorization': 'token %s' % binder['token']
            },
            body=body
        )
        response = await self.http_client.fetch(request)

        return response.body

# The Host instance to be served
HOST = Host()
