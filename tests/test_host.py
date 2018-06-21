from bindila.host import HOST
from bindila.environs import ENVIRONS


def test_parse_environ():
    assert HOST.parse_environ('gh/myorg/myrepo') == {
        'id': 'binder://gh/myorg/myrepo@master',
        'name': 'gh/myorg/myrepo',
        'version': 'master',
        'provider': 'gh',
        'org': 'myorg',
        'repo': 'myrepo'
    }

    assert HOST.parse_environ('gh/myorg/myrepo/branch') == {
        'id': 'binder://gh/myorg/myrepo@branch',
        'name': 'gh/myorg/myrepo',
        'version': 'branch',
        'provider': 'gh',
        'org': 'myorg',
        'repo': 'myrepo'
    }


def test_manifest():
    manifest = HOST.manifest()
    environs = manifest['environs']
    assert len(environs) == len(ENVIRONS)

    manifest = HOST.manifest([
        'gh/myorg/myrepo',
        'gh/myorg/myrepo/branch'
    ])
    environs = manifest['environs']
    assert len(environs) == len(ENVIRONS) + 2
    assert environs[1] == {
        'id': 'binder://gh/myorg/myrepo@branch',
        'name': 'gh/myorg/myrepo',
        'version': 'branch',
        'provider': 'gh',
        'org': 'myorg',
        'repo': 'myrepo'
    }
