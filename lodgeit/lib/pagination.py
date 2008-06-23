# -*- coding: utf-8 -*-
"""
    lodgeit.lib.pagination
    ~~~~~~~~~~~~~~~~~~~~~~

    Fancy Pagination.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import math


def generate_pagination(page, per_page, total, link_builder=None,
                        normal='<a href="%(url)s">%(page)d</a>',
                        active='<strong>%(page)d</strong>',
                        commata=',\n', ellipsis=' ...\n', threshold=3,
                        prev_link=True, next_link=True,
                        gray_prev_link=True, gray_next_link=True):
    """Generates a pagination.

    :param page:            current page number
    :param per_page:        items per page
    :param total:           total number of items
    :param link_builder:    a function which is called with a page number
                            and has to return the link to a page. Per
                            default it links to ``?page=$PAGE``
    :param normal:          template for normal (not active) link
    :param active:          template for active link
    :param commata:         inserted into the output to separate two links
    :param ellipsis:        inserted into the output to display an ellipsis
    :param threshold:       number of links next to each node (left end,
                            right end and current page)
    :param prev_link:       display back link
    :param next_link:       dipslay next link
    :param gray_prev_link:  the back link is displayed as span class disabled
                            if no backlink exists. otherwise it's not
                            displayed at all
    :param gray_next_link:  like `gray_prev_link` just for the next page link
    """
    page = int(page or 1)
    if link_builder is None:
        link_builder = lambda page: '?page=%d' % page

    was_ellipsis = False
    result = []
    pages = int(math.ceil(total / float(per_page)))
    prev = None
    next = None
    for num in xrange(1, pages + 1):
        if num - 1 == page:
            next = num
        if num + 1 == page:
            prev = num
        if num <= threshold or num > pages - threshold or \
           abs(page - num) < math.ceil(threshold / 2.0):
            if result and result[-1] != ellipsis:
                result.append(commata)
            was_space = False
            link = link_builder(num)
            template = num == page and active or normal
            result.append(template % {
                'url':      link,
                'page':     num
            })
        elif not was_ellipsis:
            was_ellipsis = True
            result.append(ellipsis)

    if next_link:
        if next is not None:
            result.append(u' <a href="%s">Next &raquo;</a>' %
                          link_builder(next))
        elif gray_next_link:
            result.append(u' <span class="disabled">Next &raquo;</span>')
    if prev_link:
        if prev is not None:
            result.insert(0, u'<a href="%s">&laquo; Prev</a> ' %
                          link_builder(prev))
        elif gray_prev_link:
            result.insert(0, u'<span class="disabled">&laquo; Prev</span> ')

    return u''.join(result)
