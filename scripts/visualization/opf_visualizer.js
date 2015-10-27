angular.module('app', []);

angular.module('app').controller('AppCtrl', ['$scope', function($scope) {

  $scope.view = {
    loadedCSV : [],
    loadedFields : [],
    renderedCSV : [],
    renderedFields : [],
    renderedFieldsToggle : [],
    graph : null,
    canRender : false
  };

  $scope.uploadFile = function(event){
    $scope.view.canRender = false;
    $scope.view.fileName = event.target.files[0].name;
    var process = function(text) {
      Papa.parse(text, {
        skipEmptyLines : true,
        header : true,
        dynamicTyping : true,
        complete: function(results) {
          $scope.view.loadedCSV = convertPapaToDyGraph(results.data);
          $scope.view.canRender = ($scope.view.loadedCSV.length !== 0) ? true : false;
          $scope.$apply();
        }
      });
    };
    convertOPFData(event.target.files[0], process);
  };

  var convertOPFData = function (data, callBack){
    var reader = new FileReader();
    reader.onload = function(file) {
      // convert to array
      var textArray = file.target.result.split(/\r\n|\n/);
      textArray.splice(1,1);
      textArray.splice(1,1);
      var text = "";
      for (var i = 0; i < textArray.length; i++) {
        text += textArray[i];
        text += "\n";
      }
      callBack(text);
    };
    reader.readAsText(data);
  };

  var scaleAnomalyScore = function(data) {
    var getMinOrMaxOfArray = function (numArray, minOrMax) {
      return Math[minOrMax].apply(null, numArray);
    };
    // get the data range - min/man
    var values = [];
    for (var i = 0; i < data.length; i++) {
      if (typeof data[i]["multiStepPredictions.actual"] === "number") {
        values.push(data[i]["multiStepPredictions.actual"]);
      }
    }
    var range = getMinOrMaxOfArray(values, "max") - getMinOrMaxOfArray(values, "min");
    // multiple each anomalyScore by this amount
    for (var x = 0; x < data.length; x++) {
      data[x].scaledAnomalyScore = data[x].anomalyScore * range;
    }
    return data;
  };

  var generateFieldMap = function(row) {
    if (!row.hasOwnProperty('timestamp')) {
      console.warn("No timestamp field was found");
      return null;
    }
    var excludes = ["reset", "timestamp", "anomalyScore", "scaledAnomalyScore"];
    angular.forEach(row, function(value, key){
      if (typeof(value) === "number" && excludes.indexOf(key) === -1 ) {
        $scope.view.loadedFields.push(key);
      }
    });
    // add timestamp, anomalyScore, and scaledAnomalyScore to the beginning of the array
    $scope.view.loadedFields = ["timestamp", "anomalyScore", "scaledAnomalyScore"].concat($scope.view.loadedFields);
    return $scope.view.loadedFields;
  };

  var convertPapaToDyGraph = function(data) {
    // use the last row in the dataset to determine the data types
    scaleAnomalyScore(data);
    var map = generateFieldMap(data[data.length - 1]);
    if (map === null) {
      return null;
    }
    for (var i = 0; i < data.length; i++) {
      var arr = [];
      for (var x = 0; x < $scope.view.loadedFields.length; x++) {
        var num;
        if (x === 0) {
          // this should always be the timestamp. See generateFieldMap
          num = new Date(data[i][$scope.view.loadedFields[x]]);
        } else {
          num = (data[i][$scope.view.loadedFields[x]] === "None") ? 0 : data[i][$scope.view.loadedFields[x]];
        }
        arr.push(num);
      }
      $scope.view.loadedCSV.push(arr);
    }
    return $scope.view.loadedCSV;
  };

  $scope.toggleVisibility = function(field) {
    $scope.view.graph.setVisibility(field.id, field.visible);
  };

  $scope.showHideAll = function(value) {
    for (var i = 0; i < $scope.view.renderedFieldsToggle.length; i++) {
      $scope.view.renderedFieldsToggle[i].visible = value;
      $scope.view.graph.setVisibility($scope.view.renderedFieldsToggle[i].id, value);
    }
  };

  $scope.renderData = function() {
    var fields = [];
    var div = document.getElementById('dataContainer');
    $scope.view.renderedCSV = angular.copy($scope.view.loadedCSV);
    $scope.view.renderedFields = angular.copy($scope.view.loadedFields);
    // build field toggle array
    $scope.view.renderedFieldsToggle.length = 0;
    var counter = 0;
    for (var i = 0; i < $scope.view.renderedFields.length; i++) {
      if ($scope.view.renderedFields[i] !== "timestamp") {
        $scope.view.renderedFieldsToggle.push({
          name : $scope.view.renderedFields[i],
          id : counter,
          visible : true
        });
        counter++;
      }
    }
    $scope.view.graph = new Dygraph(
      div,
      $scope.view.renderedCSV, {
        labels : $scope.view.renderedFields,
        animatedZooms : true,
        pointClickCallback: function(e, point) {
          timestamp = moment(point.xval);
          timestampString = timestamp.format("YYYY-MM-DD HH:mm:ss.SSS000");
          window.prompt("Copy to clipboard: Ctrl+C, Enter", timestampString);
        }
      }
    );
    document.getElementById('renderButton').blur();
  };

}]);

angular.module('app').directive('fileUploadChange', function() {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      var onChangeHandler = scope.$eval(attrs.fileUploadChange);
      element.bind('change', onChangeHandler);
      scope.$on("$destroy", function(){
        element.unbind();
      });
    }
  };
});
