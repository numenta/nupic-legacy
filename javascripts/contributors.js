(function() {
    var dataUrl = 'http://issues.numenta.org:8081/contributors.json?callback=?';
    var headers = ['Name', 'Github', 'Committer', 'Reviewer'];
    var html = '<table>\n<tr>';
    headers.forEach(function(header) {
        html += '<th>' + header + '</th>';
    });
    html += '</tr>\n';
    $.getJSON(dataUrl, function(data) {
        console.log(data);
        data.contributors.forEach(function(person) {
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
