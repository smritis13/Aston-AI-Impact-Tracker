(function () {
    "use strict";

    var myElement11 = document.getElementById('mail-main-nav');
    new SimpleBar(myElement11, { autoHide: true });

    var myElement12 = document.getElementById('mail-messages');
    new SimpleBar(myElement12, { autoHide: true });


    /* mail editor */
    var toolbarOptions = [
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
        [{ 'font': [] }],
        ['bold', 'italic', 'underline', 'strike'],        // toggled buttons
        ['blockquote', 'code-block'],

        [{ 'header': 1 }, { 'header': 2 }],               // custom button values
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],

        [{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
        [{ 'align': [] }],

        ['image', 'video'],
        ['clean']                                         // remove formatting button
    ];
    

})();