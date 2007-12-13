# -*- coding: utf-8 -*-
"""
    lodgeit.lib.antispam
    ~~~~~~~~~~~~~~~~~~~~

    Fight stupid spammers.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import re
import urllib
import time
from datetime import datetime, timedelta
from lodgeit.database import db, spam_rules, spamsync_sources


UPDATE_INTERVAL = 60 * 60 * 24 * 7


class AntiSpam(object):
    """
    Class that reads a bad content database (flat file that is automatically
    updated from the moin moin server) and checks strings against it.
    """

    def __init__(self):
        self._rules = {}
        self.sync_with_db()

    def add_sync_source(self, url):
        """Add a new sync source."""
        db.session.execute(spamsync_sources.insert(), url=url)

    def remove_sync_source(self, url):
        """Remove a sync soruce."""
        db.session.execute(spamsync_sources.delete(
                           spamsync_sources.c.url == url))

    def get_sync_sources(self):
        """Get a list of all spamsync sources."""
        return set(x.url for x in db.session.execute(
                   spamsync_sources.select()))

    def add_rule(self, rule, noinsert=False):
        """Add a new rule to the database."""
        if rule not in self._rules and rule:
            try:
                regex = re.compile(rule)
            except:
                return
            self._rules[rule] = regex
            if not noinsert:
                db.session.execute(spam_rules.insert(), rule=rule)

    def remove_rule(self, rule):
        """Remove a rule from the database."""
        self._rules.pop(rule, None)
        db.session.execute(spam_rules.delete(spam_rules.c.rule == rule))

    def get_rules(self):
        """Get a list of all spam rules."""
        return set(self._rules)

    def rule_exists(self, rule):
        """Check if a rule exists."""
        return rule in self._rules

    def sync_with_db(self, force_write=False):
        """Sync with the database."""
        # compile rules from the database and save them on the instance
        processed = set()
        for row in db.session.execute(spam_rules.select()):
            if row.rule in processed:
                continue
            processed.add(row.rule)
            self.add_rule(row.rule, noinsert=True)

        # delete out of date rules if we don't force writing
        if not force_write:
            to_delete = []
            for rule in set(self._rules) - processed:
                del self._rules[rule]
                to_delete.append(rule)
            db.session.execute(spam_rules.delete(
                spam_rules.c.rule.in_(to_delete)))

        # otherwise add the rules to the database
        else:
            for rule in set(self._rules) - processed:
                db.session.execute(spam_rules.insert(),
                                   rule=rule)

    def sync_sources(self):
        """Trigger the syncing."""
        for source in self.get_sync_sources():
            self.sync_source(source)
        self.sync_with_db(force_write=True)

    def sycn_old_sources(self):
        """Sync all older sources."""
        update_after = datetime.utcnow() - timedelta(seconds=UPDATE_INTERVAL)
        q = (spamsync_sources.c.last_update == None) | \
            (spamsync_sources.c.last_update < update_after)
        sources = list(db.session.execute(spamsync_sources.select(q)))
        if sources:
            for source in sources:
                self.sync_source(source.url)
            self.sync_with_db(force_write=True)

    def sync_source(self, url):
        """Sync one source."""
        self.load_rules(url)
        q = spamsync_sources.c.url == url
        db.session.execute(spamsync_sources.update(q),
                          last_update=datetime.utcnow())

    def load_rules(self, url):
        """Load some rules from an URL."""
        try:
            lines = urllib.urlopen(url).read().splitlines()
        except:
            return
        for line in lines:
            self.add_rule(line.strip(), noinsert=True)

    def is_spam(self, *fields):
        """Check if one of the fields provides contains spam."""
        for regex in self._rules.itervalues():
            for field in fields:
                if regex.search(field) is not None:
                    return True
        return False
