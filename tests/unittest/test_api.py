from tests import client, is_json, json
from tests.utilities.runner import testcase
from lodgeit.lib.highlighting import STYLES


def post_json(method, data=None):
    return client.post('/json/', query_string={'method': method},
                       data=data, content_type='application/json')


@testcase()
def test_json_post_and_get():
    data = '{"language": "text", "code": "hello world"}'
    resp = post_json('pastes.newPaste', data)

    assert is_json(resp)
    resp = post_json('pastes.getPaste',
                     '{"paste_id": "%d"}' % int(json(resp)['data']))
    assert is_json(resp)
    assert json(resp)['data']['code'] == "hello world"
    assert json(resp)['data']['language'] == "text"


@testcase()
def test_json_post_private_and_get():
    data = '{"language": "text", "code": "hello world", "private": "true"}'
    resp = post_json('pastes.newPaste', data)

    assert is_json(resp)
    resp = post_json('pastes.getPaste',
                     '{"paste_id": "%s"}' % json(resp)['data'])
    assert is_json(resp)
    assert json(resp)['data']['code'] == "hello world"
    assert json(resp)['data']['language'] == "text"


@testcase()
def test_json_get_last():
    data = '{"language": "text", "code": "hello world"}'
    resp = post_json('pastes.newPaste', data)
    assert is_json(resp)

    data = '{"language": "text", "code": "hello world again"}'
    resp = post_json('pastes.newPaste', data)
    assert is_json(resp)

    resp = post_json('pastes.getLast')
    assert is_json(resp)
    assert json(resp)['data']['code'] == "hello world again"
    assert json(resp)['data']['language'] == "text"


@testcase()
def test_json_get_recent():
    def run(inc):
        data = '{"language": "text", "code": "hello world %s"}' % inc
        resp = post_json('pastes.newPaste', data)
        assert is_json(resp)
        return resp

    paste_ids = []
    for x in xrange(10):
        resp = run(x)
        paste_ids.append(int(json(resp)['data']))

    resp = post_json('pastes.getRecent', '{"amount": 7}')
    assert is_json(resp)
    assert len(json(resp)['data']) == 7
    ids = [x['paste_id'] for x in json(resp)['data']]
    assert ids[::-1] == paste_ids[3:]


@testcase()
def test_json_get_styles():
    resp = post_json('styles.getStyles')
    assert is_json(resp)
    expected = [[u'%s' % x, u'%s' % STYLES[x]] for x in STYLES]
    assert json(resp)['data'] == expected
