(function() {
    var csvUrl = '../resources/contributors.csv';
    var headings = ['Name', 'Github', 'Committer', 'Reviewer'];
    var tmpl = Handlebars.compile($("#contributor-table").html());

    function csvToJson(csv) {
        var contributors = [],
            lines = csv.trim().split('\n'),
            header = lines.shift().split(',');
        lines.forEach(function(line) {
            var obj = {},
                person = line.split(',');
            header.forEach(function(key, i) {
                if (person[i] == '0') {
                    obj[key] = '';
                } else if (person[i] == '1') {
                    obj[key] = '✔';
                } else {
                    obj[key] = person[i];
                }
            });
            contributors.push(obj);
        });
        return contributors;
    }

    $.ajax(csvUrl).done(function(csv) {
        var contribs = csvToJson(csv);
        $('#contributors').html(tmpl({headings: headings, contributors: contribs}));

        $(document).ready(function() {
            $("table").tablesorter({ 
                sortList: [[3,0],[2,0],[0,0]] 
            });
            $("#tableHeaderCommitter").width(110);
            $("#tableHeaderReviewer").width(90);
            $(".tableHeaderTriangle").fadeOut(1000);
            $("thead").hover(function(){
                $(".tableHeaderTriangle").stop().fadeIn(100);
            },function(){
                setTimeout(function(){
                    $(".tableHeaderTriangle").stop().fadeOut(500);
                },1000);
            });
        });
    });

}());