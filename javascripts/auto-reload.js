(function() {
    
    window.NTA.autoReload = function(seconds) {
        var after = seconds || '30';

        setTimeout(function() {
            window.location.reload(false);
        }, after * 1000);
    
    };

}());