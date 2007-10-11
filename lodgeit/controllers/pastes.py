# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.pastes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The paste controller

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import sqlalchemy as meta

from lodgeit.application import render_template, redirect, PageNotFound, \
     Response
from lodgeit.controllers import BaseController
from lodgeit.database import Paste
from lodgeit.lib.highlighting import LANGUAGES, STYLES, get_style
from lodgeit.lib.pagination import generate_pagination


MAX_LINE_LENGTH = 300


class PasteController(BaseController):
    """
    Provides all the handler callback for paste related stuff.
    """

    def new_paste(self):
        """
        The 'create a new paste' view.
        """
        code = error = ''
        language = 'text'
        pastes = self.dbsession.query(Paste)

        if self.request.method == 'POST':
            code = self.request.form.get('code')
            language = self.request.form.get('language')
            try:
                parent = pastes.selectfirst(Paste.c.paste_id ==
                    int(self.request.form.get('parent')))
            except (KeyError, ValueError, TypeError):
                parent = None
            spam = self.request.form.get('webpage')# or \
                   #self.app.antispam.is_spam(code, language)
            if spam:
                error = 'contains spam'
            for line in code.splitlines():
                if len(line) > MAX_LINE_LENGTH:
                    error = ('your paste contains lines longer than %d '
                             'chars') % MAX_LINE_LENGTH
                    break
            if code and language and not error:
                paste = Paste(code, language, parent, self.request.user_hash)
                self.dbsession.save(paste)
                self.dbsession.flush()
                return redirect(paste.url)

        else:
            parent = self.request.args.get('reply_to')
            if parent is not None and parent.isdigit():
                parent = pastes.selectfirst(Paste.c.paste_id == parent)
                code = parent.code
                language = parent.language

        return render_template(self.request, 'new_paste.html',
            languages=LANGUAGES,
            parent=parent,
            code=code,
            language=language,
            error=error
        )

    def show_paste(self, paste_id, raw=False):
        """
        Show an existing paste.
        """
        linenos = self.request.args.get('linenos') != 'no'
        pastes = self.dbsession.query(Paste)
        paste = pastes.selectfirst(Paste.c.paste_id == paste_id)
        if paste is None:
            raise PageNotFound()
        if raw:
            return Response(paste.code, mimetype='text/plain; charset=utf-8')

        style, css = get_style(self.request)

        paste.rehighlight(linenos)

        return render_template(self.request, 'show_paste.html',
            paste=paste,
            style=style,
            css=css,
            styles=STYLES,
            linenos=linenos,
        )

    def raw_paste(self, paste_id):
        """
        Show an existing paste in raw mode.
        """
        return self.show_paste(paste_id, raw=True)

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
        raise PageNotFound()
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

        for paste in pastes:
            paste.rehighlight()

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
            old_id = self.request.form.get('old', '-1').lstrip('#')
            new_id = self.request.form.get('new', '-1').lstrip('#')
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

    def unidiff_paste(self, new_id=None, old_id=None):
        """
        Render an udiff for the two pastes.
        """
        pastes = self.dbsession.query(Paste)
        old = pastes.selectfirst(Paste.c.paste_id == old_id)
        new = pastes.selectfirst(Paste.c.paste_id == new_id)
        if old is None or new is None:
            raise PageNotFound()
        return Response(old.compare_to(new), mimetype='text/plain')

    def set_colorscheme(self):
        """
        Minimal view that updates the style session cookie. Redirects
        back to the page the user is coming from.
        """
        style_name = self.request.form.get('style')
        resp = redirect(self.request.environ.get('HTTP_REFERER') or '/')
        if style_name in STYLES:
            resp.set_cookie('style', style_name)
        return resp

controller = PasteController
