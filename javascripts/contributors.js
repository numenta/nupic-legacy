(function() {
    var csvUrl = '../resources/contributors.csv';
    var headings = ['Name', 'Github', 'Committer', 'Reviewer', 'Commits'];
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

    // Get contributor listing for initial table load.
    $.ajax(csvUrl).done(function(csv) {
        var $commitTable,
            contribs = csvToJson(csv).map(function(contributor) {
                contributor.Commits = '';
                return contributor;
            });
        
        // Fill HTML template for table structure.
        $('#contributors').html(tmpl({
            headings: headings, 
            contributors: contribs
        }));

        // Initialize the tablesorter object.
        $commitTable = $('table');
        $commitTable.tablesorter({ 
            sortList: [[3,0],[2,0],[0,0]] 
        });
        
        // Get the commit stats for incremental commit data injection into table.
        $.ajax({
            url: 'http://issues.numenta.org:8081/contribStats',
            dataType: 'jsonp',
            data: { repo: 'numenta/nupic' },
            jsonp: "callback",
            success: function(data) {
                // Inject commit stats for each record for committer
                data['numenta/nupic'].forEach(function(contributor) {
                    $commitTable.find('#' + contributor.login + ' td.commits')
                        .removeClass('small-loader')
                        .html(contributor.commits);
                });
                // Remove loader icon and replace empty commits with zero for 
                // proper sorting
                $commitTable.find('tr td.small-loader')
                    .removeClass('small-loader')
                    .html('0');
                // Trigger update on tablesorter for re-sort
                $commitTable.trigger('update');
            }
        });
    });

}());