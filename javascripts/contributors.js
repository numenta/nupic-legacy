(function() {
    var dataUrl = 'http://issues.numenta.org:8081/contributors.json?callback=?';
    var csvUrl = '../../resources/contributors.csv';
    var headers = ['Name', 'Github', 'Committer', 'Reviewer'];
    var html = '<table>\n<tr>';
    headers.forEach(function(header) {
        html += '<th>' + header + '</th>';
    });
    html += '</tr>\n';

    function csvToJson(csv) {
        var contributors = [],
            lines = csv.split('\n'),
            header = lines.shift().split(',');
        lines.forEach(function(line) {
            var obj = {},
                person = line.split(',');
            header.forEach(function(key, i) {
                if (person[i] == '0' || person[i] == '1') {
                    obj[key] = parseInt(person[i]);
                } else {
                    obj[key] = person[i];
                }
            });
            contributors.push(obj);
        });
        return contributors;
    }

    $.ajax(csvUrl).done(function(csv) {
        csvToJson(csv).forEach(function(person) {
            html += '<tr>';
            headers.forEach(function(header) {
                var value = person[header];
                if (value == 1) {
                    value = '✔';
                } else if (value == 0) {
                    value = '';
                } else if (header === 'Github') {
                    value = '<a href="https://github.com/' + value + '">' + value + '</a>';
                }
                html += '<td>' + value + '</td>';
            });
            html += '</tr>\n';
        });
        html += '</table>\n';
        $('#contributors').html(html);
    });

}());
