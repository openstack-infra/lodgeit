/*
    pastebin client scripts
    ~~~~~~~~~~~~~~~~~~~~~~~

    Lodge It pastebin client scripts.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD
*/

function togglePasteThread(uid) {
    if (Element.visible('paste_thread')) {
        new Effect.Fade('paste_thread');
        return;
    }
    new Ajax.Updater('paste_thread', '/ajax/find_paste_thread/', {
        parameters:     'paste=' + uid,
        method:         'get',
        asynchronous:   true,
        onSuccess:      function() {
            new Effect.Appear('paste_thread');
        }
    });
}

function toggleLineNumbers() {
    var el = document.getElementsByClassName('linenos')[0];
    el.style.display = (el.style.display == '') ? 'none' : '';
}

function getPasteView() {
    if (typeof _paste_view == 'undefined') {
        _paste_view = document.getElementsByClassName('syntax')[0];
    }
    return _paste_view;
}

function toggleSyntax() {
    var el = getPasteView();
    el.className = (el.className == 'plain') ? 'syntax' : 'plain';
}

function selectCode() {
    var el = getPasteView().getElementsByClassName('code')[0];
    if (document.selection) {
        var range = document.body.createTextRange();
        range.moveToElementText(el);
        range.select();
    }
    else {
        var range = document.createRange();
        range.selectNodeContents(el);
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }
}
