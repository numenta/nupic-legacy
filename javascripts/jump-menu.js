$(function() {

    var $headers = $('h2'),
        $anchor = $('#jump-menu'),
        $jumpMenu = $('<section class="jump-menu"><nav><ul></ul></nav></section>'),
        $ul = $jumpMenu.find('ul');

    if (! $anchor.length) {
        $anchor =  $('section');
    }

    $headers.each(function() {
        var $header = $(this),
            id = $header.attr('id'),
            $a = $header.find('a'),
            text = $header.html();
        if (id) {
            if ($a.length) {
                $ul.append('<li><a href="#' + id + '">' + $a.html() + '</a></li>');
            } else {
                $ul.append('<li><a href="#' + id + '">' + text + '</a></li>');
            }
        }
    });

    $anchor.prepend($jumpMenu);

});