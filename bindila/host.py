"""
Module for defining a Stencila ``Host``
"""

import datetime
import json
import re
import uuid

import pytz
import requests
import requests_mock
import sseclient
from tornado.ioloop import IOLoop

from .environs import ENVIRONS


class Host:
    """
    A Stencila ``Host``
    """

    def __init__(self):
        # A list of environs available in manifest
        # Initialized with a list of defaults
        self._environs = [self.parse_environ(environ) for environ in ENVIRONS]

        # A list of binders that have been launched by
        # this Bindila instance
        self._binders = {}

    def manifest(self, extra_environs=None):
        environs = self._environs
        if extra_environs:
            environs = [self.parse_environ(environ) for environ in extra_environs] + self._environs
        return {
            'stencila': {
                'package': 'bindila'
            },
            'environs': environs
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
        idd = 'binder://{}@{}'.format(name, ref)
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

    def launch_environ(self, environ_id, mock=False):
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
        self._binders[binder_id] = binder

        # Launch the binder asynchronously
        IOLoop.current().add_callback(self.launch_binder, binder, mock)

        # Return a local path the client can use to connect
        # to the binder
        return {
            'id': binder_id,
            'path': '/proxy/' + binder_id
        }

    def inspect_environ(self, binder_id):
        return self._binders.get(binder_id)

    async def launch_binder(self, binder, mock=False):
        """
        Launches the binder
        """

        # Build the binder URL from the environ
        environ = binder['environ']
        url = 'https://mybinder.org/build/%(provider)s/%(org)s/%(repo)s/%(version)s' % environ

        # Ask mybinder.org to launch the binder
        binder['request'] = {
            'time': datetime.datetime.now(tz=pytz.UTC).isoformat(),
            'url': url
        }
        if mock:
            with requests_mock.Mocker() as mocker:
                mocker.get(url)
                response = requests.get(url, stream=True)
        else:
            response = requests.get(url, stream=True)

        if response.status_code != 200:
            raise RuntimeError(response.text)

        # Record the event stream
        client = sseclient.SSEClient(response)
        for event in client.events():
            data = json.loads(event.data)
            data['time'] = datetime.datetime.now(tz=pytz.UTC).isoformat()
            binder['events'].append(data)
            binder['phase'] = data.get('phase')
            binder['url'] = data.get('url')
            binder['token'] = data.get('token')

    def proxy_binder(self, binder_id, path):
        """
        Proxy requests through to the binder

        Need to provide token and append `stencila-host` to URL
        e.g https://hub.mybinder.org/user/nokome-stencila-binder-u15exp4q/stencila-host
        """
        binder = self._binders.get(binder_id)
        print(binder, binder_id, path)
        return '{}'

# The Host instance to be served
HOST = Host()
