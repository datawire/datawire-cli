package DatawireState 1.0.0;

include _DatawireFS_impl.py;
include _DatawireFS_impl.js;
include io/datawire/quark/_DatawireFS_impl.java;

// WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
//
// DO NOT RELY ON THE NAME DatawireFS TOO MUCH. IT IS ABOUT TO MOVE
// INTO QUARK ITSELF.
//
// WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

namespace _DatawireFS {
    macro String dwFS_userHomeDir()
        $py{__import__('_DatawireFS_impl')._DatawireFS.userHomeDir()}
        $js{require('DatawireState/_DatawireFS_impl.js').userHomeDir()}
        $java{io.datawire.quark.runtime._DatawireFS_impl.userHomeDir()};

    macro String dwFS_fileContents(String path)
        $py{__import__('_DatawireFS_impl')._DatawireFS.fileContents($path)}
        $js{require('DatawireState/_DatawireFS_impl.js').fileContents($path)}
        $java{io.datawire.quark.runtime._DatawireFS_impl.fileContents($path)};

    class FS {
        static String userHomeDir() {
            return dwFS_userHomeDir();
        }

        static String fileContents(String path) {
            return dwFS_fileContents(path);
        }        
    }
}

namespace DatawireState {
    class DatawireState {
        bool _initialized;
        Runtime runtime;

        JSONObject object;
        JSONObject orgs;

        /*
         * _defaultOrg reflects the 'orgID' element saved in the state
         * dictionary itself.
         *
         * _currentOrg reflects the org named by the 'switchToOrg' method.
         *
         * The two start out the same, but the current org can be switched.
         */

        String _defaultOrgID;
        JSONObject _defaultOrg;

        String _currentOrgID;
        JSONObject _currentOrg;

        DatawireState() {
            self._initialized = false;
            self.runtime = concurrent.Context.runtime();
        }

        void load(String jsonInput) {
            JSONObject obj = jsonInput.parseJSON();

            if (!obj.isDefined()) {
                self.runtime.fail("DatawireState: Invalid JSON, cannot load");
            }

            JSONObject orgs = obj["orgs"];

            if (!orgs.isDefined()) {
                self.runtime.fail("DatawireState: no orgs present in input JSON!");
            }

            self.object = obj;
            self.orgs = orgs;

            obj = self.object["orgID"];

            if (!obj.isDefined()) {
                self.runtime.fail("DatawireState: no default org ID present in input JSON!");
            }

            if (!obj.isString()) {
                self.runtime.fail("DatawireState: default org ID in input JSON is not a string!");
            }

            self._defaultOrgID = obj.getString();

            obj = self.orgs[self._defaultOrgID];

            if (!obj.isDefined()) {
                self.runtime.fail("DatawireState: default org ID in input JSON is invalid!");
            }

            self._defaultOrg = obj;

            // Do switchToOrg by hand, since we're not initialized yet.
            self._currentOrgID = self._defaultOrgID;
            self._currentOrg = self._defaultOrg;

            self._initialized = true;
        }

        void switchToOrg(String orgID) {
            // If you add anything here, you'll need to revist the "Do switchToOrg by hand"
            // comment above.

            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            JSONObject org = self.orgs[orgID];

            if (!org.isDefined()) {
                self.runtime.fail("DatawireState: org " + orgID + " is not valid");
            }

            self._currentOrgID = orgID;
            self._currentOrg = org;
        }

        String getDefaultOrgID() {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._defaultOrgID;
        }

        JSONObject getDefaultOrg() {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._defaultOrg;
        }

        String getCurrentOrgID() {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._currentOrgID;
        }

        JSONObject getCurrentOrg() {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._currentOrg;
        }

        String getCurrentEmail() {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._currentOrg["email"].getString();
        }

        List<String> getCurrentServices() {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._currentOrg["service_tokens"].keys();
        }

        String getCurrentServiceToken(String service_handle) {
            if (!self._initialized) {
                self.runtime.fail("DatawireState: call load() before attempting any operations");
            }

            return self._currentOrg["service_tokens"][service_handle].getString();
        }

        String stateContents(String path) {
            return _DatawireFS.FS.fileContents(path);
        }

        String defaultStatePath() {
            return _DatawireFS.FS.userHomeDir() + "/.datawire/datawire.json";
        }

        String defaultStateContents() {
            return self.stateContents(self.defaultStatePath());
        }

        void loadDefaultState() {
            self.load(self.defaultStateContents());
        }
    }
}

