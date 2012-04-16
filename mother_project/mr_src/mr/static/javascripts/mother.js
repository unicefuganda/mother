$(function() {
  var them = $('.mrremdeleterlink').each(function(i, l) {
    var lien  = $(l);
    lien.click(deleteThisReminder);
  });
});

function deleteThisReminder(evt) {
  
}
