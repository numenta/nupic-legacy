(function() {
    var dataUrl = 'http://localhost:8081/prStatus.json?callback=?';
    var prTemplate = Handlebars.compile($("#pr-template").html());
    var $pr = $('#pullrequests');
    $.getJSON(dataUrl, function(prs) {
        $pr.html('');
        prs.forEach(function(pr) {
            console.log(pr);
            pr.latest_status = pr.statuses[0];
            var html = prTemplate(pr);
            $pr.append(html);
        });
    });
}());
