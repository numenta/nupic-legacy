// some Settings:

// TIMESTAMP:
// represents the name of the column with timestamp/x-data;
// currently such column must be present in the data, and be of ISO Date format.
// TODO: allow numeric or missing timestamp column ?
var TIMESTAMP = "timestamp";

// POSSIBLE_OPF_DATA_FIELDS:
// Is used only in OPF files during CSV parsing, where fields may, or may not be present,
// depending on the user's Model settings in NuPIC.
// If these fields are present, we'll include them as data fields.
// FIXME: is this code (and guessDataFields()) needed? 'multiStepBestPredictions.5' are
// plotted even though not in the list.
var POSSIBLE_OPF_DATA_FIELDS = ["multiStepPredictions.actual",
  "multiStepBestPredictions.actual"
];

// EXCLUDE_FIELDS:
// used to ignore some fields completely, not showing them as possibilities in graph plots.
var EXCLUDE_FIELDS = [];

// HEADER_SKIPPED_ROWS:
// number of rows (between 2nd .. Nth, included) skipped.
// For OPF this must be >= 2 (as 2nd row is 'float,float,float', 3rd: ',,' metadata)
// You can increase this (to about 2000) to skip untrained HTM predictions at the beginning
// (eg. data where anomalyScore = 0.5 at the start).
// Warning: default 2 is used, so for non-OPF data you lose the first 2 data points
// (we find that acceptable).
var HEADER_SKIPPED_ROWS = 2;

// ZOOM:
// toggle 2 methods of zooming in the graph: "RangeSelector", "HighlightSelector" (=mouse)
var ZOOM = "HighlightSelector";

// NONE_VALUE_REPLACEMENT:
// used to fix a "bug" in OPF, where some columns are numeric
// (has to be determined at the last row), but their first few values are "None".
// We replace the with this value, defaults to 0.
var NONE_VALUE_REPLACEMENT = 0;


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

  // the "Show/Hide Options" button
  $scope.toggleOptions = function() {
    $scope.view.optionsVisible = !$scope.view.optionsVisible;
    timers.resize = $timeout(function() {
      $scope.view.graph.resize();
    });
  };

  // read and parse a CSV file
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

  // show errors as "notices" in the UI
  var handleError = function(error, type, showOnce) {
    showOnce = typeof showOnce !== 'undefined' ? showOnce : false;
    exists = false;
    if (showOnce) {
      // loop through existing errors by 'message'
      errs = $scope.view.errors;
      for (var i = 0; i < errs.length; i++) {
        if (errs[i]["message"] === error) { // not unique
          return;
        }
      }
    }
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
    // strip out the rows (meta data) from header
    data.splice(0, HEADER_SKIPPED_ROWS);
    // use the last row in the dataset to determine the data types
    var map = generateFieldMap(data[data.length - 1], EXCLUDE_FIELDS);
    if (map === null) {
      handleError("Failed to parse the uploaded CSV file!", "danger");
      return null;
    }
    for (var rowId = 0; rowId < data.length; rowId++) {
      var arr = [];
      for (var colId = 0; colId < loadedFields.length; colId++) {
        var fieldValue = data[rowId][loadedFields[colId]]; // numeric
        if (colId === 0) { // this should always be the timestamp. See generateFieldMap
          if (typeof(fieldValue) === "number") {
            date = fieldValue;
          } else if (typeof(fieldValue) === "string") {
            date = parseDate(fieldValue);
          }
          if (date !== null) { // parsing succeeded, use it
            fieldValue = date;
          } else if (date === null && typeof(fieldValue) === "number") {
            handleError("Parsing timestamp failed, fallback to x-data", "warning", true);
            // keep fieldValue as is
          } else {
            handleError("Parsing timestamp failed & it is non-numeric, fallback to using iteration number", "warning", true);
            fieldValue = rowId;
          }
        } else { // process other data (non-date) columns
          // FIXME: this is an OPF "bug", should be discussed upstream
          if (fieldValue === "None") {
            fieldValue = NONE_VALUE_REPLACEMENT;
          }
        }
        arr.push(fieldValue);
      }
      loadedCSV.push(arr);
    }
  };

  // parseDate():
  // takes a string and attempts to convert it into a Date object
  // return: Date object, or null if parsing failed
  var parseDate = function(strDateTime) { // FIXME: Can using the ISO format simplify this?
    // can we get the browser to parse this successfully?
    var numDate = new Date(strDateTime);
    if (numDate.toString() !== "Invalid Date") {
      return numDate;
    }
    var dateTime = String(strDateTime).split(" "); // we are assuming that the delimiter between date and time is a space
    var args = [];
    // is the date formatted with slashes or dashes?
    var slashDate = dateTime[0].split("/");
    var dashDate = dateTime[0].split("-");
    if ((slashDate.length === 1 && dashDate.length === 1) || (slashDate.length > 1 && dashDate.length > 1)) {
      // if there were no instances of delimiters, or we have both delimiters when we should only have one
      handleError("Could not parse the timestamp", "warning", true);
      return null;
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
      handleError("There was something wrong with the date in the timestamp field.", "warning", true);
      return null;
    }
    // is there a time element?
    if (dateTime[1]) {
      var time = dateTime[1].split(":");
      args = args.concat(time);
    }
    for (var t = 0; t < args.length; t++) {
      args[t] = parseInt(args[t]);
    }
    numDate = new(Function.prototype.bind.apply(Date, [null].concat(args)));
    if (numDate.toString() === "Invalid Date") {
      handleError("The timestamp appears to be invalid.", "warning", true);
      return null;
    }
    return numDate;
  };

  // normalize select field with regards to the Data choice.
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
    // multiply each anomalyScore by this amount
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

  // say which fields will be plotted (all numeric + guessedDataFields - excluded)
  // based on parsing the last (to omit Nones at the start) row of the data.
  // return: matrix with numeric columns
  // TIMESTAMP is always the 1st column.
  var generateFieldMap = function(row, excludes) {
    if (!row.hasOwnProperty(TIMESTAMP)) {
      handleError("No timestamp field was found", "warning");
      return null;
    }
    // add all numeric fields not in excludes
    angular.forEach(row, function(value, key) {
      if (typeof(value) === "number" && excludes.indexOf(key) === -1 && key !== TIMESTAMP) {
        loadedFields.push(key);
      }
    });
    // timestamp assumed to be at the beginning of the array
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

  // the main "graphics" is rendered here
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
        labelsUTC: false, // make timestamp in UTC to have consistent graphs
        showLabelsOnHighlight: false,
        xlabel: "Time",
        ylabel: "Values",
        strokeWidth: 1,
        highlightSeriesOpts: { // series hovered get thicker
          strokeWidth: 2,
          strokeBorderWidth: 1,
          highlightCircleSize: 3
        },
        // select and copy functionality
        // FIXME: avoid the hardcoded timestamp format
        pointClickCallback: function(e, point) {
          timestamp = moment(point.xval);
          timestampString = timestamp.format("YYYY-MM-DD HH:mm:ss.SSS000");
          window.prompt("Copy to clipboard: Ctrl+C, Enter", timestampString);
        },
        // zoom functionality - toggle the 2 options in ZOOM
        animatedZooms: true,
        showRangeSelector: ZOOM === "RangeSelector",
        highlightCallback: function(e, x, points, row, seriesName) { // ZOOM === "HighlightSelector"
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
