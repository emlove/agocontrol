(function () {
    "use strict";

    var appData = Windows.Storage.ApplicationData.current.roamingSettings;
    var deviceUUID = "";
    var nav = WinJS.Navigation;

    WinJS.UI.Pages.define("/pages/itemDetail/itemDetail.html", {
        // This function is called whenever a user navigates to this page. It
        // populates the page elements with the app's data.


        ready: function (element, options) {
            
            
            var item = options && options.item ? Data.resolveItemReference(options.item) : Data.items.getAt(0);
            element.querySelector(".titlearea .pagetitle").textContent = item.group.title;
            element.querySelector("article .item-title").textContent = item.title;
            element.querySelector("article .item-subtitle").textContent = "Current Status: " + item.subtitle;
            element.querySelector("article .image").src = item.backgroundImage;
            element.querySelector("article .image").alt = item.subtitle;
            element.querySelector("article .slider").value = item.subtitle;
            element.querySelector(".content").focus();

            deviceUUID = item.deviceUUID;

            //show on and off buttons if the device is a switch
            if (item.group.title == "Switches" || item.group.title == "Dimmers") {
                var buttonsOnOff = document.getElementById("buttonsOnOff");
                buttonsOnOff.style.display = "block";
            }

            
            if (item.group.title == "Dimmers") {
                var slider = document.getElementById("slider");
                slider.style.display = "block";
            }

            //create event listeners for on and off buttons
            var buttonOn = element.querySelector("#buttonOn");
            buttonOn.addEventListener("click", this.buttonOnClick, false);

            var buttonOff = element.querySelector("#buttonOff");
            buttonOff.addEventListener("click", this.buttonOffClick, false);

            //var slider = element.querySelector("slider");
            //slider.addEventListener("");

        },

        buttonOnClick: function (mouseEvent) {
            var command = "on"
            sendCommand(command);
        },

        buttonOffClick: function (mouseEvent) {
        var command = "off";
        sendCommand(command);
    }
    });


    function sendCommand(command) {
        var serverURL = "http://" + appData.values["ip"] + ":" + appData.values["port"] + "/jsonrpc";

        var json1 = JSON.stringify({ "jsonrpc": "2.0", "method": "message", "params": { "content": { "command": command, "uuid": deviceUUID } }, "id": 1 });


        //need to wire up timeout properly
        WinJS.Promise.timeout(1500, WinJS.xhr({
            type: "POST",
            url: serverURL,
            headers: { "content-type": "application/json; charset=utf-8" },
            data: json1,
            responseType: "json",
        }).then(success, failure, progress));

    }

    function failure(response) {
       // var fail = "";
        var newData = new Data.RefreshData();
        nav.navigate("/pages/groupedItems/groupedItems.html");
        //document.getElementById('#result').innerHTML = "Cannot connect - please check settings";
    }

    function progress() {
        
        //document.getElementById('result').innerHTML = "Progress";
    }

    function success(response) {
        nav.navigate("/pages/groupedItems/groupedItems.html");
    }
})();
