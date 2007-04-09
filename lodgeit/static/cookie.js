/**
 * add very basic Cookie features to jquery
 */

jQuery.cookie = function(name, value) {
  if (typeof value != 'undefined') {
    document.cookie = name + '=' + encodeURIComponent(value);
  }
  else {
    if (document.cookie && document.cookie != '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        if (cookie.substring(0, name.length + 1) == (name + '=')) {
          return decodeURIComponent(cookie.substring(name.length + 1));
        }
      }
    }
    return null;
  }
};
