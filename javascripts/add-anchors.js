$(function() {

    $headers = $('h2,h3').each(function() {
        var $header = $(this),
            id = $header.attr('id'),
            $a = $header.find('a'),
            text = $header.html();

        if (id) {
            $header.append('&nbsp;&nbsp;&nbsp;&nbsp;<a href="#' + id + '">∞</a>');
        }

    });

});