from tests import client


def test_get_urls():
    rules = [
        ('/', 200),
        ('/all/', 200),
        ('/all/1/', 200),
        ('/xmlrpc/', 200),
        ('/json/', 200),
        ('/about/', 200),
        ('/help/', 200),
        ('/help/advanced/', 200),
        ('/help/api/', 200),
        ('/help/integration/', 200),
        ('/help/pasting/', 200),
        ('/language/de/', 302),
        ('/language/en/', 302),
        ]
    for rule, code in rules:
        resp = client.get(rule)
        assert code == resp.status_code


def test_post_url():
    resp = client.post('/')
    assert 200 == resp.status_code
