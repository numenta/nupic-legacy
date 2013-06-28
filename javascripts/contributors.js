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
    });

}());
