# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.pastes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The paste controller

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import sqlalchemy as meta

from lodgeit.application import render_template, redirect, PageNotFound
from lodgeit.controllers import BaseController
from lodgeit.database import Paste
from lodgeit.lib.highlighting import LANGUAGES, STYLES, get_style
from lodgeit.lib.pagination import generate_pagination


class PasteController(BaseController):
    """
    Provides all the handler callback for paste related stuff.
    """

    def new_paste(self):
        """
        The 'create a new paste' view.
        """
        pastes = self.dbsession.query(Paste)
        if self.request.method == 'POST':
            code = self.request.POST.get('code')
            language = self.request.POST.get('language')
            parent = self.request.POST.get('parent')
            if parent is not None:
                parent = pastes.selectfirst(Paste.c.paste_id == parent)
            if code and language:
                paste = Paste(code, language, parent, self.request.user_hash)
                self.dbsession.save(paste)
                self.dbsession.flush()
                return redirect(paste.url)

        parent = self.request.GET.get('reply_to')
        if parent is not None:
            parent = pastes.selectfirst(Paste.c.paste_id == parent)

        return render_template(self.request, 'new_paste.html',
            languages=LANGUAGES,
            parent=parent
        )

    def show_paste(self, paste_id):
        """
        Show an existing paste.
        """
        pastes = self.dbsession.query(Paste)
        paste = pastes.selectfirst(Paste.c.paste_id == paste_id)
        if paste is None:
            raise PageNotFound()
        style, css = get_style(self.request)
        return render_template(self.request, 'show_paste.html',
            paste=paste,
            style=style,
            css=css,
            styles=STYLES
        )

    def show_tree(self, paste_id):
        """
        Display the tree of some related pastes.
        """
        paste = Paste.resolve_root(self.dbsession, paste_id)
        if paste is None:
            raise PageNotFound()
        return render_template(self.request, 'paste_tree.html',
            paste=paste,
            current=paste_id
        )

    def show_all(self, page=1):
        """
        Paginated list of pages.
        """
        def link(page):
            if page == 1:
                return '/all/'
            return '/all/%d' % page

        pastes = self.dbsession.query(Paste).select(
            order_by=[meta.desc(Paste.c.pub_date)],
            limit=10,
            offset=10 * (page - 1)
        )
        if not pastes and page != 1:
            raise PageNotFound()

        return render_template(self.request, 'show_all.html',
            pastes=pastes,
            pagination=generate_pagination(page, 10,
                Paste.count(self.request.engine), link),
            css=get_style(self.request)[1]
        )

    def compare_paste(self, new_id=None, old_id=None):
        """
        Render a diff view for two pastes.
        """
        # redirect for the compare form box
        if old_id is new_id is None:
            old_id = self.request.POST.get('old', '-1').lstrip('#')
            new_id = self.request.POST.get('new', '-1').lstrip('#')
            return redirect('/compare/%s/%s' % (old_id, new_id))
        pastes = self.dbsession.query(Paste)
        old = pastes.selectfirst(Paste.c.paste_id == old_id)
        new = pastes.selectfirst(Paste.c.paste_id == new_id)
        if old is None or new is None:
            raise PageNotFound()
        return render_template(self.request, 'compare_paste.html',
            old=old,
            new=new,
            diff=old.compare_to(new, template=True)
        )

    def set_colorscheme(self):
        """
        Minimal view that updates the style session cookie. Redirects
        back to the page the user is coming from.
        """
        style_name = self.request.POST.get('style')
        resp = redirect(self.request.environ.get('HTTP_REFERER') or '/')
        if style_name in STYLES:
            resp.set_cookie('style', style_name)
        return resp

controller = PasteController
