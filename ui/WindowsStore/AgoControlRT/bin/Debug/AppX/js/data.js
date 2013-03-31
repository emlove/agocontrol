(function () {
    "use strict";

    
    var appData = Windows.Storage.ApplicationData.current.roamingSettings;
    var nav = WinJS.Navigation;
    var list = new WinJS.Binding.List();

    var groupedItems = list.createGrouped(
        function groupKeySelector(item) { return item.group.key; },
        function groupDataSelector(item) { return item.group; }
    );


    errorChecking();

        var serverURL = "http://" + appData.values["ip"] + ":" + appData.values["port"] + "/jsonrpc";

        var jsonString = JSON.stringify({ "jsonrpc": "2.0", "method": "message", "params": { "content": { "command": "inventory" } }, "id": 2 });

        WinJS.xhr({
            type: "POST",
            url: serverURL,
            headers: { "content-type": "application/json; charset=utf-8" },
            data: jsonString,
            responseType: "json",
        }).then(success, failure, progress);


    // this is called from external js files each time the devices need to be refreshed
    WinJS.Namespace.define("Data", {
        RefreshData : WinJS.Class.define(
        function refreshData() {
            errorChecking();
            //make sure list is cleared to stop duplicate device entries
            list.splice(0, list.length);
            list._currentKey = 0;
        

                var serverURL = "http://" + appData.values["ip"] + ":" + appData.values["port"] + "/jsonrpc";

                var json1 = JSON.stringify({ "jsonrpc": "2.0", "method": "message", "params": { "content": { "command": "inventory" } }, "id": 2 });

                WinJS.xhr({
                    type: "POST",
                    url: serverURL,
                    headers: { "content-type": "application/json; charset=utf-8" },
                    data: json1,
                    responseType: "json",
                }).then(success, failure, progress);

        })});

    function errorChecking() {
        //this sets IP and port if blank, code needed to check if blank and display options screen
        //then this should be obsolete
        if (appData.values["ip"] == "") {
            appData.values["ip"] = "192.168.1.15";
        }
        if (appData.values["port"] == "") {
            appData.values["port"] = "8008";
        }
    }

    function failure() {
        var fail = "";
        //document.getElementById('result').innerHTML = "Failure";
    }

    function progress() {
        
        //document.getElementById('result').innerHTML = "Progress";
    }

    function success(response) {
        
        // You can add data from asynchronous sources whenever it becomes available.
        generateSampleData(response).forEach(function (item) {
            
            list.push(item);
        });
    }

    WinJS.Namespace.define("Data", {
        items: groupedItems,
        groups: groupedItems.groups,
        getItemReference: getItemReference,
        getItemsFromGroup: getItemsFromGroup,
        resolveGroupReference: resolveGroupReference,
        resolveItemReference: resolveItemReference
    });

    // Get a reference for an item, using the group key and item title as a
    // unique reference to the item that can be easily serialized.
    function getItemReference(item) {
        return [item.group.key, item.title];
    }

    // This function returns a WinJS.Binding.List containing only the items
    // that belong to the provided group.
    function getItemsFromGroup(group) {
        return list.createFiltered(function (item) { return item.group.key === group.key; });
    }

    // Get the unique group corresponding to the provided group key.
    function resolveGroupReference(key) {
        for (var i = 0; i < groupedItems.groups.length; i++) {
            if (groupedItems.groups.getAt(i).key === key) {
                return groupedItems.groups.getAt(i);
            }
        }
    }

    // Get a unique item from the provided string array, which should contain a
    // group key and an item title.
    function resolveItemReference(reference) {
        for (var i = 0; i < groupedItems.length; i++) {
            var item = groupedItems.getAt(i);
            if (item.group.key === reference[0] && item.title === reference[1]) {
                return item;
            }
        }
    }

    // Returns an array of devices that can be added to the application's
    // data list. 
    function generateSampleData(response) {

        // This sets the image location for each group and device
        var temperatureImage = "images/temperature.png";
        var switchImage = "images/switch.png";
        var phoneImage = "images/phone.png";
        var dimmerImage = "images/dimmer.png";
        var otherImage = "images/questionMark.png";


        // Each of these groups must have a unique key to be displayed separately.
        var deviceGroups = [
            { key: "group1", title: "Multisensors", subtitle: "List of multisensors", backgroundImage: temperatureImage  },
            { key: "group2", title: "Switches", subtitle: "List of switches", backgroundImage: switchImage },
            { key: "group3", title: "Phones", subtitle: "List of phones", backgroundImage: phoneImage },
            { key: "group4", title: "Dimmers", subtitle: "List of dimmers", backgroundImage: dimmerImage },
            { key: "group5", title: "Other Devices", subtitle: "List of other devices", backgroundImage: otherImage },
        ];

        // Each of these devices should have a reference to a particular group.
        var deviceItems = [];
        deviceItems.length = 0;

        var json2 = JSON.parse(response.responseText);
        var inventory = json2.result.inventory;
        var picture = "";

        var inventoryArray = [];
        inventoryArray.length = 0;

        //this ain't going to work for dimmers?
        for (var prop in inventory) {
            var inventoryStuff = inventory[prop];

            switch (inventoryStuff.state) {
                case "0":
                    inventoryStuff.state = "Off";
                    break;
                case "255":
                    inventoryStuff.state = "On";
                    break;
                default:
                    inventoryStuff.state = inventoryStuff.state;
                    break;
            }

            switch (inventoryStuff.devicetype) {
                case "switch":
                    deviceItems.push({ group: deviceGroups[1], title: inventoryStuff.name, subtitle: inventoryStuff.state, backgroundImage: switchImage, deviceUUID: prop });
                    break;
                case "multilevelsensor":
                    deviceItems.push({ group: deviceGroups[0], title: inventoryStuff.name, subtitle: inventoryStuff.state, backgroundImage: temperatureImage, deviceUUID: prop });
                   break;
                case "phone":
                    deviceItems.push({ group: deviceGroups[2], title: inventoryStuff.name, subtitle: inventoryStuff.state, backgroundImage: phoneImage, deviceUUID: prop });
                     break;
                case "dimmer":
                    deviceItems.push({ group: deviceGroups[3], title: inventoryStuff.name, subtitle: inventoryStuff.state, backgroundImage: dimmerImage, deviceUUID: prop });
                    break;
                default:
                    deviceItems.push({ group: deviceGroups[4], title: inventoryStuff.name, subtitle: inventoryStuff.state, backgroundImage: otherImage, deviceUUID: prop });
                    break;
            }
        }
        return deviceItems;
    }
})();
