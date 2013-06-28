(function() {
    var dataUrl = 'http://issues.numenta.org:8081/prStatus.json?callback=?';
    var prTemplate = Handlebars.compile($("#pr-template").html());
    var emptyPrTemplate = Handlebars.compile($("#empty-pr-template").html());
    var $pr = $('#pullrequests');
    $.getJSON(dataUrl, function(prs) {
        $pr.html('');
        if (prs.length) {
            prs.forEach(function(pr) {
                console.log(pr);
                pr.latest_status = pr.statuses[0];
                var html = prTemplate(pr);
                $pr.append(html);
            });
        } else {
            $pr.html(emptyPrTemplate());
        }
    });
}());
