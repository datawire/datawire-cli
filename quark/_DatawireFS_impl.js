(function () {
    "use strict";

    var os = require('os');
    var fs = require('fs');

    var quark = require('quark').quark;

    var _DatawireFS = (function () {
        function _DatawireFS() {}

        _DatawireFS.userHomeDir = function () {
            return os.homedir();
        };

        _DatawireFS.fileContents = function (path) {
            try {
                return fs.readFileSync(path, 'utf-8');
            }
            catch (e) {
                var runtime = quark.concurrent.Context.runtime();
                runtime.fail("failure reading " + path + ": " + e)
            }
        };

        return _DatawireFS;
    })();

    module.exports = _DatawireFS;
})();
