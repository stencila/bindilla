import datetime
import json
import re

import pytz
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from .environs import ENVIRONS

class Host:
    """
    A Stencila `Host` that launches, and then proxies to, a container on Binder.
    """

    def __init__(self, binder_host='https://mybinder.org', proxy=True):
        """
        Construct a host.

        :param binder_host: The Binder host URL. Usually `https://mybinder.org` but could
                            be some other deployment of Binder.
        :param proxy: Should this proxy requests to the Binder container or just
                      return a URL to connect directly to it?
        """

        # A list of default environs available in manifest
        self._environs = [self.parse_environ(environ) for environ in ENVIRONS]

        # The Binder host URL.
        self._binder_host = binder_host

        # Switch proxying on/off.
        self._proxy = proxy

        # An asychronous HTTP client used to talk to Binder and
        # the containers that it hosts
        # Use CurlAsyncHTTPClient because the default failed to run inside the Docker container
        # for some reason
        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        self._http_client = AsyncHTTPClient()

    def manifest(self, extra_environs=None):
        """
        Return the manifest for this host.
        """
        environs = self._environs
        if extra_environs:
            environs = [self.parse_environ(environ) for environ in extra_environs] + self._environs
        return {
            'stencila': {
                'package': 'bindilla'
            },
            'environs': environs,
            # Properties expected by the client
            'types': [],  # v0 API
            'services': []  # v1 API
        }

    @staticmethod
    def parse_environ(environ_id):
        """
        Parse an environ id into an environment spec to include in manifest.

        Also split out the parts needed for a Binder repo path, which have the pattern
          `<provider-name>/<org-name>/<repo-name>/<branch|commit|tag>`
        The `<branch|commit|tag> part is optional and defaults to `master`.
        """
        match = re.match(r'^https?:\/\/(.+)', environ_id)
        if match:
            parts = match.group(1).split('/')
            if len(parts) < 3:
                raise ValueError('Environment id does not have enough parts in path: %s' % environ_id)
        else:
            raise ValueError('Environment id does not appear to be a URL: %s' % environ_id)

        providers = {
            'github.com': 'gh',
            'gitlab.com': 'gl'
        }
        provider = providers.get(parts[0])
        if not provider:
            raise ValueError('Environment provider should be one of: %s' % ', '.join(providers.keys()))

        org = parts[1]
        repo = parts[2]
        ref = parts[3] if len(parts) == 4 else 'master'
        name = '{}/{}/{}'.format(provider, org, repo)

        return {
            # Properties required by Host API
            'id': environ_id,
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
        Launch an environment on Binder.

        This sends a request to Binder to create a new container based on the
        environment identifier.
        """

        # Parse the environ id string into an environ spec
        environ = self.parse_environ(environ_id)

        # Record the binder's details so that we can record
        # events associated with it and retrieve them using `inspect`
        binder = {
            'environ': environ,
            'phase': None,
            'events': []
        }

        def handle_stream(events):
            """
            Handle the SSE event stream from Binder
            """
            events = events.decode().split('\n')
            for event in events:
                if ":" in event:
                    (field, value) = event.split(":", 1)
                    field = field.strip()
                    if field == 'data':
                        try:
                            data = json.loads(value)
                        except ValueError as error:
                            raise error
                        else:
                            data['time'] = datetime.datetime.now(tz=pytz.UTC).isoformat()
                            binder['events'].append(data)
                            binder['phase'] = data.get('phase')
                            binder['id'] = data.get('url')
                            binder['token'] = data.get('token')

        # Build the binder URL from the environ
        environ = binder['environ']
        url = self._binder_host + '/build/%(provider)s/%(org)s/%(repo)s/%(version)s' % environ

        # Request container from the Binder host
        binder['request'] = {
            'time': datetime.datetime.now(tz=pytz.UTC).isoformat(),
            'url': url
        }
        request = HTTPRequest(
            url=url,
            method='GET',
            headers={'content-type': 'text/event-stream'},
            request_timeout=0,
            streaming_callback=handle_stream
        )
        await self._http_client.fetch(request)

        # Determine which URL the client should use to connect to the Binder container
        binder_id = binder['id']
        if binder_id[-1] == '/':
            binder_id = binder_id[:-1]
        if self._proxy:
            # Use a local path on this server to proxy to the binder (suppling token etc)
            binder['path'] = '/proxy/' + binder_id + '@' + binder['token']
        else:
            # Use the URL of the binder to connect to the remote host directly
            # (requires that there is no token required on the binder)
            binder['url'] = binder_id + '/stencila-host'

        return binder

    async def proxy_environ(self, method, binder_id, token, path, body=None): #pylint: disable=too-many-arguments
        """
        Proxy requests through to the binder.

        This methods appends `/stencila-host` to the Binder container's URL
        e.g https://hub.mybinder.org/user/org-repo-mukdlnm5/stencila-host
        and puts the token into the header for authorization.
        """

        url = binder_id + '/stencila-host/' + path
        request = HTTPRequest(
            url=url,
            method=method,
            headers={
                'Authorization': 'token %s' % token
            },
            body=body
        )
        return await self._http_client.fetch(request)

# The Host instance to be served
HOST = Host()
