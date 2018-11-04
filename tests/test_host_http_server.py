import json

from bindilla.host_http_server import HOST, make
from tornado.testing import AsyncHTTPTestCase


class TestIndex(AsyncHTTPTestCase):
    def get_app(self):
        return make()

    def test_index(self):
        response = self.fetch('/')
        self.assertEqual(response.code, 200)


class TestV0App(AsyncHTTPTestCase):
    def get_app(self):
        return make()

    def test_manifest(self):
        response = self.fetch('/v0/manifest')
        self.assertEqual(response.code, 200)
        self.assertEqual(json.loads(response.body), HOST.manifest())

        environs = [
            'gh/org1/repo1',
            'gh/org2/repo2'
        ]
        url = '/{}/v0/manifest'.format(
            ','.join(environs)
        )
        response = self.fetch(url)
        self.assertEqual(response.code, 200)
        self.assertEqual(json.loads(response.body), HOST.manifest(environs))
