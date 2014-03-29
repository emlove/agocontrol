/**
 * The plugin model
 * @returns {agoeinkPlugin}
 */
function agoeinkPlugin() {
    document.getElementById("col-right").className = "twelve columns";
    var self = this;

    this.devices = deviceMap;

    this.hasNavigation = ko.observable(false);

    this.placedDevices = ko.observable([]);


    self.findDevice = function(uuid) {
        for ( var i = 0; i < self.devices.length; i++) {
            if (self.devices[i].uuid == uuid) {
                return self.devices[i];
            }
        }
    };


    /* Load the floorplan data into the grid */
        if (self.devices.length == 0) {
            return;
        }
        var list = currentFloorPlan();
        var result = self.placedDevices();
        for ( var k in list) {
            if (k == "name" || k == "uuid") {
                continue;
            }
            var x = list[k].x;
            var y = list[k].y;
            if (x < 0 || y < 0) {
                continue;
            }
            if (result[x] === undefined) {
                result[x] = [];
            }
            result[x][y] = self.findDevice(k);
        }
        self.placedDevices([]);
        self.placedDevices(result);


    this.firstRow = ko.computed(function() {
        var result = [];
        var x = 0;
        for ( var y = 0; y < 3; y++) {
            if (self.placedDevices()[x] !== undefined && self.placedDevices()[x][y] !== undefined) {
                result.push(self.placedDevices()[x][y]);
            } else {
                result.push({
                    devicetype : "placeholder",
                    x : x,
                    y : y
                });
            }
        }

        return result;
    });

    this.secondRow = ko.computed(function() {
        var result = [];
        var x = 1;
        for ( var y = 0; y < 3; y++) {
            if (self.placedDevices()[x] !== undefined && self.placedDevices()[x][y] !== undefined) {
                result.push(self.placedDevices()[x][y]);
            } else {
                result.push({
                    devicetype : "placeholder",
                    x : x,
                    y : y
                });
            }
        }

        return result;
    });

    this.thirdRow = ko.computed(function() {
        var result = [];
        var x = 2;
        for ( var y = 0; y < 3; y++) {
            if (self.placedDevices()[x] !== undefined && self.placedDevices()[x][y] !== undefined) {
                result.push(self.placedDevices()[x][y]);
            } else {
                result.push({
                    devicetype : "placeholder",
                    x : x,
                    y : y
                });
            }
        }

        return result;
    });

    buildfloorPlanList(this);

}

/**
 * Entry point: mandatory!
 */
function init_plugin()
{
    model = new agoeinkPlugin();

    model.deviceTemplate = function(item) {
        if (supported_devices.indexOf(item.devicetype) != -1) {
            return templatePath + "devices/" + item.devicetype;
        }

        return templatePath + "devices/empty";
    }.bind(model);


    model.mainTemplate = function() {
	return templatePath + "agoeink";
    }.bind(model);
    ko.applyBindings(model);
}
