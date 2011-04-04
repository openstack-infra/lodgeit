from tests import client
from tests.utilities.runner import testcase


def post_json(method, data=None):
    return client.post('/json/', query_string={'method': method},
                       data=data, content_type='application/json')


@testcase()
def test_json_post_and_get():
    data = '{"language": "text", "code": "hello world"}'
    resp = post_json('pastes.newPaste', data)

    assert resp.is_json
    resp = post_json('pastes.getPaste',
                     '{"paste_id": "%d"}' % int(resp.json['data']))
    assert resp.is_json
    assert resp.json['data']['code'] == "hello world"
    assert resp.json['data']['language'] == "text"


@testcase()
def test_json_post_private_and_get():
    data = '{"language": "text", "code": "hello world", "private": "true"}'
    resp = post_json('pastes.newPaste', data)

    assert resp.is_json
    resp = post_json('pastes.getPaste',
                     '{"paste_id": "%s"}' % resp.json['data'])
    assert resp.is_json
    assert resp.json['data']['code'] == "hello world"
    assert resp.json['data']['language'] == "text"


@testcase()
def test_json_get_last():
    data = '{"language": "text", "code": "hello world"}'
    resp = post_json('pastes.newPaste', data)
    assert resp.is_json

    data = '{"language": "text", "code": "hello world again"}'
    resp = post_json('pastes.newPaste', data)
    assert resp.is_json

    resp = post_json('pastes.getLast')
    assert resp.is_json
    assert resp.json['data']['code'] == "hello world again"
    assert resp.json['data']['language'] == "text"


@testcase()
def test_json_get_recent():
    def run(inc):
        data = '{"language": "text", "code": "hello world %s"}' % inc
        resp = post_json('pastes.newPaste', data)
        assert resp.is_json
        return resp

    paste_ids = []
    for x in xrange(10):
        resp = run(x)
        paste_ids.append(int(resp.json['data']))

    resp = post_json('pastes.getRecent', '{"amount": 7}')
    assert resp.is_json
    assert len(resp.json['data']) == 7
    ids = [x['paste_id'] for x in resp.json['data']]
    assert ids[::-1] == paste_ids[3:]


@testcase()
def test_json_get_styles():
    styles = [
        ['monokai', 'Monokai'],
        ['manni', 'Manni'],
        ['perldoc', 'Perldoc'],
        ['borland', 'Borland'],
        ['colorful', 'Colorful'],
        ['default', 'Default'],
        ['murphy', 'Murphy'],
        ['trac', 'Trac'],
        ['tango', 'Tango'],
        ['vim', 'Vim'],
        ['autumn', 'Autumn'],
        ['vs', 'Vs'],
        ['emacs', 'Emacs'],
        ['friendly', 'Friendly'],
        ['bw', 'Bw'],
        ['pastie', 'Pastie'],
        ['fruity', 'Fruity'],
        ['native', 'Native'],
        ]
    resp = post_json('styles.getStyles')
    assert resp.is_json
    assert resp.json['data'] == styles
