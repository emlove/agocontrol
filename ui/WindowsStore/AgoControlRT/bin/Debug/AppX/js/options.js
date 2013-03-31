(function () {
    "use strict";

    var appData = Windows.Storage.ApplicationData.current.roamingSettings;

    WinJS.UI.Pages.define("/pages/settings/options.html", {
        // This function is called whenever a user navigates to this page. It
        // populates the page elements with the app's data.
        ready: function (element, options) {

            // Set settings to existing values
            if (appData.values.size > 0) {
                if(appData.values["ip"]){
                    ip.value = appData.values["ip"];
                }
                if(appData.values["port"]){
                    port.value = appData.values["port"];
                }

           }

            // Wire up on change events for settings controls
            ip.onchange = function () {
                appData.values["ip"] = ip.value;
            };
            port.onchange = function () {
                appData.values["port"] = port.value;
            };
        },

        unload: function () {
            // Respond to navigations away from this page.
        },

        updateLayout: function (element, viewState, lastViewState) {
            // Respond to changes in viewState.
        }
    });

})();