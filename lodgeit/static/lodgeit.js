/**
 * LodgeIt JavaScript Module
 *
 * addes fancy and annoying javascript effects to that page
 * but hey. now it's web2.0!!!!111
 */
var LodgeIt = {

  _toggleLock : false,
  
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

    /* hide all related blocks if in js mode */
    $('div.related div.content').hide();
    
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

$(document).ready(LodgeIt.init);
