/**
 * Model class
 * 
 * @returns {floorPlan}
 */
function floorPlan() {
    var self = this;
    this.devices = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);

    this.page = ko.observable(1);

    this.rooms = ko.computed(function() {
	var roomMap = [];
	for ( var room in rooms) {
	    roomMap[room] = rooms[room];
	    roomMap[room].devices = ko.observableArray([]);
	}
	roomMap['none'] = {
	    name : "No Room",
	    devices : ko.observableArray([])
	};

	for ( var i = 0; i < self.devices().length; i++) {
	    if (roomMap[self.devices()[i].roomUID] !== undefined) {
		roomMap[self.devices()[i].roomUID].devices.push(self.devices()[i]);
	    } else {
		roomMap['none'].devices.push(self.devices()[i]);
	    }
	}

	var result = [];
	for ( var room in rooms) {
	    result.push(roomMap[room]);
	}
	if (result.length > 0) {
	    result.push(roomMap['none']);
	}

	return result;
    });

    self.findDevice = function(uuid) {
	for ( var i = 0; i < self.devices().length; i++) {
	    if (self.devices()[i].uuid == uuid) {
		return self.devices()[i];
	    }
	}
    };

    /* Load the floorplan data into the grid */
    this.devSubscription = 0;
    this.devSubscription = this.devices.subscribe(function() {
	if (self.devices().length == 0) {
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
	self.devSubscription.dispose();
	self.devSubscription = 0;
    });

    this.placedDevices = ko.observable([]);

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

    this.saveDevicePos = function(uuid, x, y) {
	var content = {};
	content.command = "setdevicefloorplan";
	content.floorplan = currentFloorPlan().uuid;
	content.device = uuid;
	content.uuid = agoController;
	content.x = x;
	content.y = y;
	sendCommand(content);
    };

    this.postRender = function() {
	$('.dnd-device').each(function() {
	    $(this).draggable({
		cursor : "move",
		revert : true,
		helper : function(event) {
		    return $('<div style="z-Index: 999; text-align:center; color:#FFF; width: 58px; height: 58px;" class="pretty large primary btn grid-item-icon"></div>');
		}
	    });
	});

	$('.device').each(function() {
	    $(this).draggable({
		cursor : "move",
		handle : ".handle",
		revert : true,
		helper : function(event) {
		    return $('<div style="z-Index: 999; text-align:center; color:#FFF;' + 'width: 58px; height: 58px;" class="pretty large primary btn grid-item-icon"></div>');
		}
	    });
	});

	$('.drop-target').each(function() {
	    $(this).droppable({
		drop : function(event, ui) {
		    var x = $(this).data("x");
		    var y = $(this).data("y");
		    var uuid = ui.draggable.data("uuid");
		    console.debug("dropped:" + uuid + " on " + x + " / " + y);
		    var tmp = self.placedDevices();
		    /* Remove old entry if any */
		    for ( var i = 0; i < tmp.length; i++) {
			if (tmp[i] === undefined) {
			    continue;
			}
			for ( var j = 0; j < tmp[i].length; j++) {
			    if (tmp[i][j] !== undefined && tmp[i][j].uuid == uuid) {
				tmp[i][j] = undefined;
			    }
			}
		    }
		    /* Add the new one */
		    for ( var i = 0; i < self.devices().length; i++) {
			if (self.devices()[i].uuid == uuid) {
			    if (tmp[x] === undefined) {
				tmp[x] = [];
			    }
			    tmp[x][y] = self.devices()[i];
			    self.saveDevicePos(uuid, x, y);
			    self.placedDevices([]);
			    self.placedDevices(tmp);
			}
		    }
		}
	    });
	});

	$('.placeholder').each(function() {
	    $(this).css("cursor", "default");
	});

    };

    this.afterTreeView = function() {
	$('.tree li').each(function() {
	    if ($(this).children('ul').length > 0) {
		$(this).addClass('parent');
	    }
	});

	$('.tree li.parent > a').unbind('click');
	$('.tree li.parent > a').click(function() {
	    $(this).parent().toggleClass('active');
	    $(this).parent().children('ul').slideToggle('fast');
	});

	$('.device_tree').droppable({
	    drop : function(event, ui) {
		var uuid = ui.draggable.data("uuid");
		var tmp = self.placedDevices();
		for ( var i = 0; i < tmp.length; i++) {
		    if (tmp[i] === undefined) {
			continue;
		    }
		    for ( var j = 0; j < tmp[i].length; j++) {
			if (tmp[i][j] !== undefined && tmp[i][j].uuid == uuid) {
			    tmp[i][j] = undefined;
			    self.saveDevicePos(uuid, -1, -1);
			}
		    }
		}
		self.placedDevices([]);
		self.placedDevices(tmp);
	    }
	});

	self.postRender();
    };

    buildfloorPlanList(this);
}

/**
 * Initalizes the model
 */
function init_floorPlan() {
    model = new floorPlan();

    model.deviceTemplate = function(item) {
	if (supported_devices.indexOf(item.devicetype) != -1) {
	    return 'devices/' + item.devicetype;
	}
	return 'devices/empty';
    }.bind(model);

    model.mainTemplate = function() {
	return "floorplan";
    }.bind(model);

    model.navigation = function() {
	return "navigation/treenav";
    }.bind(model);

    ko.applyBindings(model);
}

function createFloorPlan() {
    var content = {};
    content.command = "setfloorplanname";
    content.uuid = agoController;
    content.name = window.prompt("Please enter a name for the floorplan", "FloorPlan Name");
    if (!content.name) {
	return;
    }
    sendCommand(content, function(r) {
	document.location.href = "?floorplan&fp=" + r.result.uuid;
    });
}