from tests import client


def test_load_most_urls():
    rules = ['/',
             '/compare/',
             '/all/',
             '/all/1/',
             '/xmlrpc/',
             '/json/',
             '/about/',
             '/help/',
             '/help/json/',
             '/colorscheme/',
             '/language/es/']
    for rule in rules:
        client.get(rule)
