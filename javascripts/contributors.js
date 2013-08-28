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
        function addCommits(commitData) {
            console.log(commitData)
            var contribs = csvToJson(csv).map(function(thisContributor){
                var thisContributorCommitData = $.grep(commitData['numenta/nupic'], function(nextObj){
                    return nextObj.login == thisContributor.Github
                });
                if (thisContributorCommitData.length) {
                    thisContributor.Commits = thisContributorCommitData.shift().commits;
                    if (thisContributor.Commits == 0) {
                        thisContributor.Commits = '';
                    }
                }
                return thisContributor;
            });
            headings.push('Commits');
            $('#contributors').html(tmpl({headings: headings, contributors: contribs}));

            $(document).ready(function() {
                $("table").tablesorter({ 
                    sortList: [[3,0],[2,0],[0,0]] 
                });
                $("#tableHeaderCommitter").width(88);
                $("#tableHeaderReviewer").width(78);
                $("#tableHeaderCommits").width(77);
                $(".tableHeaderTriangle").fadeOut(1000);
                $("th").hover(function(){
                    //if($('thead').data('hover')) {
                        $(".tableHeaderTriangle").stop().fadeIn(100);
                    //}
                },function(){
                    setTimeout(function(){
                        if(!($('thead').data('hover'))) {
                            $(".tableHeaderTriangle").stop();
                            $(".tableHeaderTriangle").fadeOut(500);
                        }
                    },1000);
                });
                $("thead").hover(
                    function() { $.data(this, 'hover', true); },
                    function() { $.data(this, 'hover', false); }
                ).data('hover', false);
            });

        }
        $.ajax({
            url: 'http://issues.numenta.org:8081/contribStats',
            dataType: 'jsonp',
            data: { repo: 'numenta/nupic' },
            success: function(data) { addCommits(data); },
            jsonp: "callback"
        });
    });

}());