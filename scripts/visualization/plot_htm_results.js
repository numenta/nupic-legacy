function getFilePaths(path){
  $.ajax({
    url: path,
    async: false,
    success: function (csvd) {
        filePaths = $.csv2Array(csvd);
    },
    dataType: "text",
});
  return filePaths
}

function createDiv(container, id){
  id = "graphdiv" + id
  var div = document.createElement("div");
  div.id = id
  div.className = "graph"
  container[0].appendChild(div)
  return div
}


function render(path) {
  filePaths = getFilePaths(path)
  if (event.keyCode != 13)
    return

  graphs = [];
  var graphDiv = document.getElementsByClassName("graphContainer");

  while(graphDiv[0].firstChild) graphDiv[0].removeChild(graphDiv[0].firstChild)

  var query = document.getElementById("query").value;
  var count = 0;

  var blockRedraw = false;

  for (var i = 0; i < filePaths.length; i++) {
    path = filePaths[i][0]
    if (path.indexOf(query) > -1) {
      graphs.push(
        new Dygraph(
          createDiv(graphDiv, count++),
          path,
          {
            visibility: [true, true, true, false, true],
            series: {
              timestamp: {
                axis: "x1"
              },
              value: {
                axis: "y1"
              },
              label: {
                axis: "y2"
              },
              anomaly_score: {
                axis: "y2"
              },
              _raw_score: {
                axis: "y2"
              },
              _alerts: {
                axis: "y2"
              }
            },
            legend: "always",
            title: path,
            drawCallback: function (me, initial) {
              if (blockRedraw || initial) return;
              blockRedraw = true;
              var range = me.xAxisRange();
              var yrange = me.yAxisRange();

              for (var j = 0; j < selected.length; j++) {
                if (graphs[j] == me) continue;
                graphs[j].updateOptions({
                  dateWindow: range,
                  valueRange: yrange
                });
              }
              blockRedraw = false;
            },
            pointClickCallback: function(e, point) {
              timestamp = moment(new Date(point.xval));
              timestampString = timestamp.format("YYYY-MM-DD HH:mm:ss.SSS000");
              window.prompt("Copy to clipboard: Ctrl+C, Enter", timestampString);
            },
            underlayCallback: function(canvas, area, g) {
              var rowVal = g.getValue(0,1);
              var rowTime = g.getValue(0,0);

              var left = g.toDomCoords(rowTime, rowVal)[0];

              // probationary period
              row = Math.min(Math.round(0.15 * g.numRows()), 750);
              rowVal = g.getValue(row,1);
              rowTime = g.getValue(row,0);

              var right = g.toDomCoords(rowTime, rowVal)[0]

              canvas.fillStyle = "rgba(150, 150, 150, 1.0)";
              canvas.fillRect(left, area.y, right - left, area.h);
            }
          }
        )
      );
    }
  }
}
