(function() {
    var dataUrl = 'http://issues.numenta.org:8081/maillist.json?callback=?';
    
    function convertToDygraph(data) {
        var sum = 0;
        return data.messages.byMonth.map(function(monthData) {
            sum += monthData.number;
            return [
                new Date(monthData.year, monthData.month), 
                monthData.number,
                sum
            ];
        });
    }

    $.getJSON(dataUrl, function(data) {
        new Dygraph(
            document.getElementById('stats'),
            convertToDygraph(data),
            {
                title: 'Mailing List Statistics By Month',
                labels: ['Date', 'Month', 'Cumulative']
            }
        );
    });
}());
