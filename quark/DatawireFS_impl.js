(function () {
    "use strict";

    var os = require('os');
    var fs = require('fs');

    var quark = require('quark').quark;

    var DatawireFS = (function () {
        function DatawireFS() {}

        DatawireFS.userHomeDir = function () {
            return os.homedir();
        };

        DatawireFS.fileContents = function (path) {
            try {
                return fs.readFileSync(path, 'utf-8');
            }
            catch (e) {
                var runtime = quark.concurrent.Context.runtime();
                runtime.fail("failure reading " + path + ": " + e)
            }
        };

        return DatawireFS;
    })();

    module.exports = DatawireFS;
})();
