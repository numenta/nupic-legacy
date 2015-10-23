angular.module('app', []);

angular.module('app').controller('AppCtrl', ['$scope', '$http', function($scope, $http) {

  $scope.view = {
    data : {
      data : [],
      selectedPath : null,
      fields : [],
      graph : null
    },
    results : {
      data : [],
      selectedPath : null,
      fields : [],
      graph : null
    }
  };

  var removeBlankPaths = function(csvs) {
    for (var i = csvs.length - 1; i >= 0; i--) {
      if (csvs[i] === "") {
        csvs.splice(i, 1);
      }
    }
    return csvs;
  };

  var removePath = function(path) {
    var pathParts = path.split("/");
    return pathParts[pathParts.length - 1];
  };

  var createCsvPathObject = function(csvs) {
    csvs = removeBlankPaths(csvs);
    var newPaths = [];
    for (var i = 0; i < csvs.length; i++) {
      newPaths.push({
        name: removePath(csvs[i]),
        path: csvs[i]
      });
    }
    return newPaths;
  };

  $scope.canRender = function() {
    return $scope.view.data.selectedPath !== null || $scope.view.results.selectedPath !== null;
  };

  $scope.renderData = function(name) {
    // get fields
    $http.get($scope.view[name].selectedPath.path).then(function(response){
      // success
      generateFields(name, response.data);
      var div = document.getElementById(name + 'Container');
      render(name, div, $scope.view[name].selectedPath);
    }, function(error){
      // failure
      console.log("There was an error loading the data: ", response.status);
    });
  };

  $scope.toggleVisibility = function(name, field) {
    $scope.view[name].graph.setVisibility(field.id, field.visible);
  };

  var generateFields = function(name, csv) {
    var lines = csv.split("\n");
    var fields = lines[0].split(",");
    $scope.view[name].fields.length = 0;
    // remove timestamp
    for (var i = 0; i < fields.length; i++) {
      if (fields[i].toLowerCase() !== "timestamp") {
        $scope.view[name].fields.push({
          name : fields[i],
          visible : true,
          id : null
        });
      }
    }
    // apply the ids
    for (var x = 0; x < $scope.view[name].fields.length; x++) {
      $scope.view[name].fields[x].id = x;
    }
  };

  var render = function(name, div, csv) {
    $scope.view[name].graph = new Dygraph(
      div,
      csv.path, {
        clickCallback: function(e, x, points) {
          timestamp = moment(new Date(x));
          timestampString = timestamp.format("YYYY-MM-DD HH:mm:ss.SSS000");
          window.prompt("Copy to clipboard: Ctrl+C, Enter", timestampString);
        }
      }
    );
  };

  $http.get('data_file_paths.txt').then(function(response) {
    // success
    $scope.view.data.data = createCsvPathObject(response.data.split("\n"));
  }, function(response) {
    // failure
    console.log("There was an error loading the data paths: ", response.status);
  });
  $http.get('results_file_paths.txt').then(function(response) {
    // success
    $scope.view.results.data = createCsvPathObject(response.data.split("\n"));
  }, function(response) {
    // failure
    console.log("There was an error loading the data paths: ", response.status);
  });


}]);
