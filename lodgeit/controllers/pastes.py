# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.pastes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The paste controller

    :copyright: 2007-2008 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
from werkzeug import redirect, Response
from werkzeug.exceptions import NotFound
from lodgeit import local
from lodgeit.lib import antispam
from lodgeit.i18n import list_languages as i18n_list_languages, _
from lodgeit.utils import render_to_response, url_for
from lodgeit.models import Paste
from lodgeit.database import session
from lodgeit.lib.highlighting import list_languages, STYLES, get_style
from lodgeit.lib.captcha import check_hashed_solution, Captcha


class PasteController(object):
    """Provides all the handler callback for paste related stuff."""

    #XXX:dc: using language here clashes with internationalization terms
    def new_paste(self, language=None):
        """The 'create a new paste' view."""
        language = local.request.args.get('language', language)
        if language is None:
            language = local.request.session.get('language', 'text')

        code = error = ''
        show_captcha = private = False
        parent = None
        req = local.request
        getform = req.form.get

        if local.request.method == 'POST':
            code = getform('code', u'')
            language = getform('language')
            parent_id = getform('parent')
            spam = getform('webpage') or antispam.is_spam(code)

            if spam:
                error = _('your paste contains spam')
                captcha = getform('captcha')
                if captcha:
                    if check_hashed_solution(captcha):
                        error = None
                    else:
                        error = _('your paste contains spam and the '
                                  'CAPTCHA solution was incorrect')
                show_captcha = True

            if code and language and not error:
                paste = Paste(code, language, parent_id, req.user_hash,
                              'private' in req.form)
                session.add(paste)
                session.commit()
                local.request.session['language'] = language
                if paste.private:
                    identifier = paste.private_id
                else:
                    identifier = paste.paste_id
                return redirect(url_for('pastes/show_paste',
                                        identifier=identifier))
        else:
            parent_id = req.values.get('reply_to')
            if parent_id is not None:
                parent = Paste.get(parent_id)
                if parent is not None:
                    code = parent.code
                    language = parent.language
                    private = parent.private
        return render_to_response('new_paste.html',
            languages=list_languages(),
            parent=parent,
            code=code,
            language=language,
            error=error,
            show_captcha=show_captcha,
            private=private
        )

    def show_paste(self, identifier, raw=False):
        """Show an existing paste."""
        linenos = local.request.args.get('linenos') != 'no'
        paste = Paste.get(identifier)
        if paste is None:
            raise NotFound()
        if raw:
            return Response(paste.code, mimetype='text/plain; charset=utf-8')

        style, css = get_style(local.request)
        return render_to_response('show_paste.html',
                                  paste=paste,
                                  style=style,
                                  css=css,
                                  styles=STYLES,
                                  linenos=linenos,
                                  new_replies=Paste.fetch_replies(),
                                  )

    def raw_paste(self, identifier):
        """Show an existing paste in raw mode."""
        return self.show_paste(identifier, raw=True)

    def show_tree(self, identifier):
        """Display the tree of some related pastes."""
        paste = Paste.resolve_root(identifier)
        if paste is None:
            raise NotFound()
        return render_to_response('paste_tree.html',
            paste=paste,
            current=identifier
        )

    def compare_paste(self, new_id=None, old_id=None):
        """Render a diff view for two pastes."""
        getform = local.request.form.get
        # redirect for the compare form box
        if old_id is None:
            old_id = getform('old', '-1').lstrip('#')
            new_id = getform('new', '-1').lstrip('#')
            return redirect(url_for('pastes/compare_paste',
                                    old_id=old_id, new_id=new_id))

        old = Paste.get(old_id)
        new = Paste.get(new_id)
        if old is None or new is None:
            raise NotFound()

        return render_to_response('compare_paste.html',
            old=old,
            new=new,
            diff=old.compare_to(new, template=True)
        )

    def unidiff_paste(self, new_id=None, old_id=None):
        """Render an udiff for the two pastes."""
        old = Paste.get(old_id)
        new = Paste.get(new_id)

        if not (old or new):
            raise NotFound()

        return Response(old.compare_to(new), mimetype='text/plain')

    def set_colorscheme(self):
        """Minimal view that updates the style session cookie. Redirects
        back to the page the user is coming from.
        """
        style_name = local.request.form.get('style')
        resp = redirect(local.request.headers.get('referer') or
                        url_for('pastes/new_paste'))
        #XXX:dc: use some sort of form element validation instead
        if style_name in STYLES:
            resp.set_cookie('style', style_name)
        return resp

    def set_language(self, lang='en'):
        """Minimal view that sets a different language. Redirects
        back to the page the user is coming from."""
        for key, value in i18n_list_languages():
            if key == lang:
                local.request.set_language(lang)
                break
        return redirect(local.request.headers.get('referer') or
                        url_for('pastes/new_paste'))

    def rss(self):
        query = Paste.find_all()
        items = query.all()
        return render_to_response('rss.html', items=items,
                                  mimetype='application/rss+xml')

    def show_captcha(self):
        """Show a captcha."""
        return Captcha().get_response(set_cookie=True)

controller = PasteController
