/**
 * LodgeIt JavaScript Module
 *
 * addes fancy and annoying javascript effects to that page
 * but hey. now it's web2.0!!!!111
 */

String.prototype.startsWith = function(str){
    return (this.indexOf(str) === 0);
}

var LodgeIt = {

  _toggleLock : false,
  insertTabs : false,
  
  init : function() {
    /**
     * make textarea 1px height and save the value for resizing
     * in a variable.
     */
    var textarea = $('textarea');
    var submitform = $('form.submitform');
    var textareaHeight = $.cookie('ta_height');
    if (textareaHeight) {
      textareaHeight = parseInt(textareaHeight);
    }
    else {
      textareaHeight = textarea.height();
    }
    submitform.hide();
    textarea.css('height', '1px');

    $('input', $('#insert_tabs').show())
      .change(function() {
        LodgeIt.insertTabs = this.checked;
      });

    /* tab insertion handling */
    textarea.keydown(function(e) {
      if (!LodgeIt.insertTabs)
        return;
      if (e.keyCode == 9 && !e.ctrlKey && !e.altKey) {
        if (this.setSelectionRange) {
          var
            start = this.selectionStart,
            end = this.selectionEnd,
            top = this.scrollTop;
          this.value = this.value.slice(0, start) + '\t' +
                       this.value.slice(end);
          this.setSelectionRange(start + 1, start + 1);
          this.scrollTop = top;
          e.preventDefault();
        }
        else if (document.selection.createRange) {
          this.selection = document.selection.createRange();
          this.selection.text = '\t';
          e.returnValue = false;
        }
      }
    });

    /* hide all related blocks if in js mode */
    $('div.related div.content').hide();

    /* hide all filter related blocks if in js mode */
    var paste_filter = $('div.paste_filter form');
    if (paste_filter.length && !paste_filter.is('.open'))
      paste_filters.hide();
    
    /**
     * links marked with "autoclose" inside the related div
     * use some little magic to get an auto hide animation on
     * click, before the actual request is sent to the browser.
     */
    $('div.related div.content a.autoclose').each(function() {
      this.onclick = function() {
        var href = this.getAttribute('href');
        $('div.related div.content').slideUp(300, function() {
          document.location.href = href;
        });
        return false;
      };
    });

    /**
     * and here we do something similar for the forms. block
     * submitting until the close animation is done.
     */
    $('div.related form').each(function() {
      var submit = false;
      var self = this;
      this.onsubmit = function() {
        if (submit)
          return true;
        $('div.related div.content').slideUp(300, function() {
          submit = true;
          self.submit();
        });
        return false;
      };
    });

    /**
     * now where everything is done resize the textarea
     * we do this at the end to speed things up on slower systems
     * this code is only used for the frontpage.
     */
    textarea.animate({
      height: textareaHeight
    }, textareaHeight * 1.2, 'linear', function() {
      textarea[0].focus();
    });
    submitform.fadeIn(textareaHeight, function() {
      // small workaround in order to not slow firefox down
      submitform.css('opacity', 'inherit');
    });
  },


  /**
   * slide-toggle the related links box
   */
  toggleRelatedBox : function() {
    if (!this._toggleLock) {
      this._toggleLock = true;
      $('div.related div.content').slideToggle(500, function() {
        LodgeIt._toggleLock = false;
      });
    }
  },

  /**
   * slide-toggle a box
   */
  toggleFilterBox : function() {
    $('div.paste_filter form').slideToggle(500);
  },

  /**
   * fade the line numbers in and out
   */
  toggleLineNumbers : function() {
    $('#paste').toggleClass('nolinenos');
  },

  /**
   * Textarea resizer helper
   */
  resizeTextarea : function(step) {
    var textarea = $('textarea');
    var oldHeight = textarea.height();
    var newHeight = oldHeight + step;
    if (newHeight >= 100) {
      $.cookie('ta_height', newHeight);
      textarea.animate({
        height: newHeight
      }, 200);
    }
  },

  /**
   * hide the notification box
   */
  hideNotification : function() {
    $('div.notification').slideUp(300);
  },

  /**
   * remove user hash cookie
   */
  removeCookie : function() {
    if (confirm('Do really want to remove your cookie?')) {
      $.cookie('lodgeit_session', '');
      alert('Your cookie was resetted!');
    }
  }
};

$(document).ready(function() {
  LodgeIt.init;

  /* Autocomplete languages */

  var languages = [];
  var ids = [];

  var multiFileInfo = $('#multi-file-information').hide();

  $('form.submitform select[name="language"] option').each(function() {
    ids.push($(this).val());
    languages.push($(this).text());
  });

  var new_input = $('<input type="text" name="language" value="Text only">')
    .autocomplete(languages)
    .result(function(event, data) {
      if (data[0].toLowerCase().startsWith('multi'))
        multiFileInfo.fadeIn();
      else
        multiFileInfo.fadeOut('fast');
    })
    .click(function() { $(this).val(''); });
  $('form.submitform select[name="language"]').replaceWith($(new_input));

  /* Bind a processable value to the input field on submitting */
  $('form.submitform').submit(function() {
    new_input.val(ids[$.inArray(new_input.val(), languages)]);
  });
 
});
