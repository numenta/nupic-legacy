// some Settings:

// TIMESTAMP: 
// represents the name of the column with timestamp/x-data;
// currently such column must be present in the data, and be of ISO Date format.
// TODO: allow numeric or missing timestamp column ?
var TIMESTAMP = "timestamp"; 

// POSSIBLE_OPF_DATA_FIELDS: 
// Is used only in OPF files during CSV parsing, where fields may, or may not be present, 
// depending on the user's Model settings in NuPIC. 
// Iff these fields are present, we'll include them as data fields. 
// FIXME: is this code (and guessDataFields()) needed? 'multiStepBestPredictions.5' are
// plotted even though not in the list.
var POSSIBLE_OPF_DATA_FIELDS = ["multiStepPredictions.actual", 
                                "multiStepBestPredictions.actual"];


// Web UI:

angular.module('app', ['ui.bootstrap']);

angular.module('app').controller('AppCtrl', ['$scope', '$timeout', function($scope, $timeout) {

  $scope.view = {
    fieldState: [],
    graph: null,
    canRender: false,
    dataField: null,
    optionsVisible: true,
    loadedFileName: "",
    renderedFileName: "",
    errors: []
  };

  var loadedCSV = [],
    loadedFields = [],
    renderedCSV,
    renderedFields,
    backupCSV,
    timers = {};

  $scope.toggleOptions = function() {
    $scope.view.optionsVisible = !$scope.view.optionsVisible;
    timers.resize = $timeout(function() {
      $scope.view.graph.resize();
    });
  };

  $scope.uploadFile = function(event) {
    $scope.view.canRender = false;
    $scope.view.loadedFileName = event.target.files[0].name;
    loadedCSV.length = 0;
    loadedFields.length = 0;
    Papa.parse(event.target.files[0], {
      skipEmptyLines: true,
      header: true,
      dynamicTyping: true,
      complete: function(results) {
        convertPapaToDyGraph(results.data);
        $scope.view.canRender = (loadedCSV.length > 0) ? true : false;
        $scope.$apply();
      },
      error: function(error) {
        handleError(error, "danger");
      }
    });
  };

  var handleError = function(error, type) {
    $scope.view.errors.push({
      "message": error,
      "type": type
    });
  };

  $scope.clearErrors = function() {
    $scope.view.errors.length = 0;
  };

  $scope.clearError = function(id) {
    $scope.view.errors.splice(id, 1);
  };

  var convertPapaToDyGraph = function(data) {
    // since this is OPF data, strip out the second and third rows
    data.splice(0, 2);
    // use the last row in the dataset to determine the data types
    var map = generateFieldMap(data[data.length - 1]);
    if (map === null) {
      return null;
    }
    for (var i = 0; i < data.length; i++) {
      var arr = [];
      for (var x = 0; x < loadedFields.length; x++) {
        var num;
        if (x === 0) {
          // this should always be the timestamp. See generateFieldMap
          var args = [];
          var dateTime =  data[i][loadedFields[x]].split(" ");
          // is the date formatted with slashes or dashes?
          var slashDate = dateTime[0].split("/");
          var dashDate = dateTime[0].split("-");
          if ((slashDate.length === 1 && dashDate.length === 1) || (slashDate.length > 1 && dashDate.length > 1)) {
            // if there were no instances of delimiters, or we have both delimiters when we should only have one
            handleError("Could not parse the timestamp", "warning");
            return;
          }
          // if it is a dash date, it is probably in this format: yyyy:mm:dd
          if (dashDate.length > 2) {
            args.push(dashDate[0]);
            args.push(dashDate[1]);
            args.push(dashDate[2]);
          }
          // if it is a slash date, it is probably in this format: mm/dd/yy
          else if (slashDate.length > 2) {
            args.push(slashDate[2]);
            args.push(slashDate[0]);
            args.push(slashDate[1]);
          } else {
            handleError("There was something wrong with the date in the timestamp field.", "warning");
            return;
          }
          // is there a time element?
          if (dateTime[1]) {
            var time = dateTime[1].split(":");
            args = args.concat(time);
          }
          for (var t = 0; t < args.length; t++) {
            args[t] = parseInt(args[t]);
          }
          num = new (Function.prototype.bind.apply(Date, [null].concat(args)));
          if (num.toString() === "Invalid Date") {
            handleError("The timestamp appears to be invalid.", "warning");
            return;
          }
        } else {
          num = (data[i][loadedFields[x]] === "None") ? 0 : data[i][loadedFields[x]];
        }
        arr.push(num);
      }
      loadedCSV.push(arr);
    }
  };

  $scope.normalizeField = function(normalizedFieldId) {
    // we have to add one here, because the data array is different than the label array
    var fieldId = normalizedFieldId + 1;
    if ($scope.view.dataField === null) {
      console.warn("No data field is set");
      return;
    }
    var dataFieldId = parseInt($scope.view.dataField) + 1;
    var getMinOrMaxOfArray = function(numArray, minOrMax) {
      return Math[minOrMax].apply(null, numArray);
    };
    // get the data range - min/man
    var dataFieldValues = [];
    var toBeNormalizedValues = [];
    for (var i = 0; i < renderedCSV.length; i++) {
      if (typeof renderedCSV[i][dataFieldId] === "number" && typeof renderedCSV[i][fieldId] === "number") {
        dataFieldValues.push(renderedCSV[i][dataFieldId]);
        toBeNormalizedValues.push(renderedCSV[i][fieldId]);
      }
    }
    var dataFieldRange = getMinOrMaxOfArray(dataFieldValues, "max") - getMinOrMaxOfArray(dataFieldValues, "min");
    var normalizeFieldRange = getMinOrMaxOfArray(toBeNormalizedValues, "max") - getMinOrMaxOfArray(toBeNormalizedValues, "min");
    var ratio = dataFieldRange / normalizeFieldRange;
    // multiple each anomalyScore by this amount
    for (var x = 0; x < renderedCSV.length; x++) {
      renderedCSV[x][fieldId] = parseFloat((renderedCSV[x][fieldId] * ratio).toFixed(10));
    }
    $scope.view.graph.updateOptions({
      'file': renderedCSV
    });
  };

  $scope.denormalizeField = function(normalizedFieldId) {
    var fieldId = normalizedFieldId + 1;
    for (var i = 0; i < renderedCSV.length; i++) {
      renderedCSV[i][fieldId] = backupCSV[i][fieldId];
    }
    $scope.view.graph.updateOptions({
      'file': renderedCSV
    });
  };

  $scope.renormalize = function() {
    for (var i = 0; i < $scope.view.fieldState.length; i++) {
      if ($scope.view.fieldState[i].normalized) {
        $scope.normalizeField($scope.view.fieldState[i].id);
      }
    }
  };

  var updateValue = function(fieldName, value) {
    for (var f = 0; f < $scope.view.fieldState.length; f++) {
      if ($scope.view.fieldState[f].name === fieldName) {
        $scope.view.fieldState[f].value = value;
        break;
      }
    }
  };

  var setDataField = function(fieldName) {
    for (var i = 0; i < $scope.view.fieldState.length; i++) {
      if ($scope.view.fieldState[i].name === fieldName) {
        $scope.view.dataField = $scope.view.fieldState[i].id;
        break;
      }
    }
  };

  var setColors = function(colors) {
    for (var c = 0; c < colors.length; c++) {
      $scope.view.fieldState[c].color = colors[c];
    }
  };

  var guessDataField = function(possibleDataFields) {
    for (var i = 0; i < $scope.view.fieldState.length; i++) {
      if (possibleDataFields.indexOf($scope.view.fieldState[i].name) > -1) {
        $scope.view.dataField = $scope.view.fieldState[i].id;
        break;
      }
    }
  };

  var generateFieldMap = function(row) {
    if (!row.hasOwnProperty(TIMESTAMP)) {
      handleError("No timestamp field was found", "warning");
      return null;
    }
    var excludes = ["reset", TIMESTAMP];
    angular.forEach(row, function(value, key) {
      if (typeof(value) === "number" && excludes.indexOf(key) === -1) {
        loadedFields.push(key);
      }
    });
    // add timestamp, anomalyScore, and scaledAnomalyScore to the beginning of the array
    loadedFields.unshift(TIMESTAMP);
    return loadedFields;
  };

  $scope.toggleVisibility = function(field) {
    $scope.view.graph.setVisibility(field.id, field.visible);
    if (!field.visible) {
      field.value = null;
    }
  };

  $scope.showHideAll = function(value) {
    for (var i = 0; i < $scope.view.fieldState.length; i++) {
      $scope.view.fieldState[i].visible = value;
      $scope.view.graph.setVisibility($scope.view.fieldState[i].id, value);
      if (!value) {
        $scope.view.fieldState[i].value = null;
      }
    }
  };

  $scope.renderData = function() {
    var fields = [];
    var div = document.getElementById("dataContainer");
    renderedCSV = angular.copy(loadedCSV);
    backupCSV = angular.copy(loadedCSV);
    renderedFields = angular.copy(loadedFields);
    $scope.view.renderedFileName = $scope.view.loadedFileName;
    // build field toggle array
    $scope.view.fieldState.length = 0;
    $scope.view.dataField = null;
    var counter = 0;
    for (var i = 0; i < renderedFields.length; i++) {
      if (renderedFields[i] !== TIMESTAMP) {
        $scope.view.fieldState.push({
          name: renderedFields[i],
          id: counter,
          visible: true,
          normalized: false,
          value: null,
          color: "rgb(0,0,0)"
        });
        counter++;
      }
    }
    guessDataField(POSSIBLE_OPF_DATA_FIELDS);
    $scope.view.graph = new Dygraph(
      div,
      renderedCSV, {
        labels: renderedFields,
        showRangeSelector: true,
        showLabelsOnHighlight: false,
        pointClickCallback: function(e, point) {
          timestamp = moment(point.xval);
          timestampString = timestamp.format("YYYY-MM-DD HH:mm:ss.SSS000");
          window.prompt("Copy to clipboard: Ctrl+C, Enter", timestampString);
        },
        highlightCallback: function(e, x, points, row, seriesName) {
          for (var p = 0; p < points.length; p++) {
            updateValue(points[p].name, points[p].yval);
          }
          $scope.$apply();
        },
        drawCallback: function(graph, is_initial) {
          if (is_initial) {
            setColors(graph.getColors());
          }
        }
      }
    );
    document.getElementById("renderButton").blur();
  };

  $scope.$on("$destroy", function() {
    angular.forEach(timers, function(timer) {
      $timeout.cancel(timer);
    });
  });

}]);

angular.module('app').directive('fileUploadChange', function() {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
      var onChangeHandler = scope.$eval(attrs.fileUploadChange);
      element.bind('change', onChangeHandler);
      scope.$on("$destroy", function() {
        element.unbind();
      });
    }
  };
});

angular.module('app').directive('opfField', function() {
  return {
    restrict: 'A',
    scope: false,
    template: '<td><input type="checkbox" ng-disabled="field.id === view.dataField || view.dataField === null" ng-model="field.normalized"></td>' +
      '<td><input type="radio" ng-disabled="field.normalized" ng-model="view.dataField" ng-value="{{field.id}}"></td>',
    link: function(scope, element, attrs) {
      var watchers = {};
      watchers.normalized = scope.$watch('field.normalized', function(newValue, oldValue) {
        if (newValue) {
          scope.normalizeField(scope.field.id);
        } else {
          scope.denormalizeField(scope.field.id);
        }
      });
      watchers.isData = scope.$watch('view.dataField', function() {
        scope.renormalize();
      });
      scope.$on("$destroy", function() {
        angular.forEach(watchers, function(watcher) {
          watcher();
        });
      });
    }
  };
});
