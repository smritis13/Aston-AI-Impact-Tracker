(function() {
    "use strict";

    var myElement1 = document.getElementById('files-main-nav');
    new SimpleBar(myElement1, { autoHide: true });

    var myElement2 = document.getElementById('file-folders-container');
    new SimpleBar(myElement2, { autoHide: true });



})();