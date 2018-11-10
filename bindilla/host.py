import datetime
import json
import re
import uuid

import pytz
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

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

        # A list of binders that have been launched by
        # this Bindilla instance. Needed for the proxying.
        self._binders = {}

        # An asychronous HTTP client used to talk to Binder and
        # the containers that it hosts
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
    def parse_environ(binder_path):
        """
        Parse a Binder path into a Stencila environment spec.

        Binder repo paths have the pattern `<provider-name>/<org-name>/<repo-name>/<branch|commit|tag>`
        The `<branch|commit|tag> part is optional and defaults to `master`.
        """
        parts = binder_path.split('/')
        if len(parts) < 3:
            raise ValueError('Invalid Binder repo path %s' % binder_path)

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
        Launch an environment on Binder.

        This sends a request to Binder to create a new container based on the
        environment identifier.
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

        def handle_stream(event):
            """
            Handle the SSE event stream from Binder
            """
            event = event.decode()
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
                        binder['base_url'] = data.get('url')
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
        if self._proxy:
            # Use a local path on this server to proxy to the binder (suppling token etc)
            binder['path'] = '/proxy/' + binder_id
        else:
            # Use the URL of the binder to connect to the remote host directly
            # (requires that there is no token required on the binder)
            if binder.get('base_url'):
                binder['url'] = binder['base_url'] + 'stencila-host'

        self._binders[binder_id] = binder

        return binder

    def inspect_environ(self, binder_id):
        """
        Get details about a binder.
        """
        return self._binders.get(binder_id)

    async def proxy_environ(self, method, binder_id, path, body=None):
        """
        Proxy requests through to the binder.

        This methods appends `/stencila-host` to the Binder container's URL
        e.g https://hub.mybinder.org/user/org-repo-mukdlnm5/stencila-host
        and puts the token into the header for authorization.
        """
        binder = self._binders.get(binder_id)
        if not binder:
            raise ValueError('No such binder: {}'.format(binder_id))

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
        response = await self._http_client.fetch(request)

        return response.body

# The Host instance to be served
HOST = Host()
