from bindila.host import Host
from bindila.environs import ENVIRONS
from tornado.ioloop import IOLoop


def test_parse_environ():
    host = Host()

    assert host.parse_environ('gh/myorg/myrepo') == {
        'id': 'binder://gh/myorg/myrepo/master',
        'name': 'gh/myorg/myrepo',
        'version': 'master',
        'provider': 'gh',
        'org': 'myorg',
        'repo': 'myrepo'
    }

    assert host.parse_environ('gh/myorg/myrepo/branch') == {
        'id': 'binder://gh/myorg/myrepo/branch',
        'name': 'gh/myorg/myrepo',
        'version': 'branch',
        'provider': 'gh',
        'org': 'myorg',
        'repo': 'myrepo'
    }


def test_manifest():
    host = Host()

    manifest = host.manifest()
    environs = manifest['environs']
    assert len(environs) == len(ENVIRONS)

    manifest = host.manifest([
        'gh/myorg/myrepo',
        'gh/myorg/myrepo/branch'
    ])
    environs = manifest['environs']
    assert len(environs) == len(ENVIRONS) + 2
    assert environs[1] == {
        'id': 'binder://gh/myorg/myrepo/branch',
        'name': 'gh/myorg/myrepo',
        'version': 'branch',
        'provider': 'gh',
        'org': 'myorg',
        'repo': 'myrepo'
    }


def test_launch_environ():
    host = Host()

    assert len(host._binders) == 0

    ioloop = IOLoop.current()

    async def run():
        result = await host.launch_environ('binder://gh/org1/repo1')
        ioloop.call_later(0.5, ioloop.stop)

    ioloop.add_callback(run)
    ioloop.start()

    assert len(host._binders) == 1

    binder = next(iter(host._binders.values()))
    assert 'request' in binder
    assert binder['request']['url'] == 'https://mybinder.org/build/gh/org1/repo1/master'
    assert binder['events'] == []
