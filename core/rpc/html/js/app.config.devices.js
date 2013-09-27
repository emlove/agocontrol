/**
 * Model class
 * 
 * @returns {deviceConfig}
 */
function deviceConfig() {
    var self = this;
    this.devices = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);

    this.roomFilters = ko.observableArray([]);
    this.deviceTypeFilters = ko.observableArray([]);

    this.devices.subscribe(function() {
	var tagMap = {};
	for ( var i = 0; i < self.devices().length; i++) {
	    var dev = self.devices()[i];
	    if (tagMap["type_" + dev.devicetype]) {
		tagMap["type_" + dev.devicetype].w++;
	    } else {
		tagMap["type_" + dev.devicetype] = {
		    type : "device",
		    value : dev.devicetype,
		    w : 1,
		    className : "default label"
		};
	    }
	    if (dev.room) {
		if (tagMap["room_" + dev.room]) {
		    tagMap["room_" + dev.room].w++;
		} else {
		    tagMap["room_" + dev.room] = {
			type : "room",
			value : dev.room,
			w : 1,
			className : "default label"
		    };
		}
	    }
	}

	var devList = [];
	var roomList = [];

	for ( var k in tagMap) {
	    var entry = tagMap[k];
	    if (entry.type == "device") {
		devList.push(entry);
	    } else {
		roomList.push(entry);
	    }
	}

	devList.sort(function(a, b) {
	    return b.w - a.w;
	});

	roomList.sort(function(a, b) {
	    return b.w - a.w;
	});

	self.roomFilters(roomList);
	self.deviceTypeFilters(devList);
    });

    this.addFilter = function(item) {
	if (item.type == "device") {
	    for ( var i = 0; i < self.deviceTypeFilters().length; i++) {
		if (self.deviceTypeFilters()[i].value == item.value) {
		    self.deviceTypeFilters()[i].className = item.className == "default label" ? "primary label" : "default label";
		}
	    }
	    var tmp = self.deviceTypeFilters();
	    self.deviceTypeFilters([]);
	    self.deviceTypeFilters(tmp);
	} else {
	    for ( var i = 0; i < self.roomFilters().length; i++) {
		if (self.roomFilters()[i].value == item.value) {
		    self.roomFilters()[i].className = item.className == "default label" ? "primary label" : "default label";
		}
	    }
	    var tmp = self.roomFilters();
	    self.roomFilters([]);
	    self.roomFilters(tmp);
	}

	var eTable = $("#configTable").dataTable();
	self.resetFilter();

	var escapeRegExp = function(str) {
	    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
	};

	var filters = [];
	for ( var i = 0; i < self.deviceTypeFilters().length; i++) {
	    var tmp = self.deviceTypeFilters()[i];
	    if (tmp.className == "primary label") {
		filters.push(escapeRegExp(tmp.value));
	    }
	}
	if (filters.length > 0) {
	    eTable.fnFilter("^(" + filters.join("|") + ")$", 2, true, false);
	}

	var filters = [];
	for ( var i = 0; i < self.roomFilters().length; i++) {
	    var tmp = self.roomFilters()[i];
	    if (tmp.className == "primary label") {
		filters.push(escapeRegExp(tmp.value));
	    }
	}
	if (filters.length > 0) {
	    eTable.fnFilter("^(" + filters.join("|") + ")$", 1, true, false);
	}
    };

    this.resetFilter = function() {
	var eTable = $("#configTable").dataTable();
	var oSettings = eTable.fnSettings();
	for ( var i = 0; i < oSettings.aoPreSearchCols.length; i++) {
	    oSettings.aoPreSearchCols[i].sSearch = "";
	}
	oSettings.oPreviousSearch.sSearch = "";
	eTable.fnDraw();
    };

    this.makeEditable = function() {
	var eTable = $("#configTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#configTable").dataTable();
	eTable.$('td.edit_device').editable(function(value, settings) {
	    var content = {};
	    content.device = $(this).data('uuid');
	    content.uuid = agoController;
	    content.command = "setdevicename";
	    content.name = value;
	    sendCommand(content);
	    return value;
	}, {
	    data : function(value, settings) {
		return value;
	    },
	    onblur : "cancel"
	});

	eTable.$('td.select_device_room').editable(function(value, settings) {
	    var content = {};
	    content.device = $(this).parent().data('uuid');
	    content.uuid = agoController;
	    content.command = "setdeviceroom";
	    content.room = value == "unset" ? "" : value;
	    sendCommand(content);
	    return value == "unset" ? "unset" : rooms[value].name;
	}, {
	    data : function(value, settings) {
		var list = {};
		list["unset"] = "--";
		for ( var uuid in rooms) {
		    list[uuid] = rooms[uuid].name;
		}

		return JSON.stringify(list);
	    },
	    type : "select",
	    onblur : "submit"
	});

	$.unblockUI();
    };
}

/**
 * Initalizes the model
 */
function init_deviceConfig() {

    $.blockUI({
	message : '<div>Please wait ...</div>',
	css : {
	    border : '3px solid #a00'
	}
    });

    model = new deviceConfig();

    model.mainTemplate = function() {
	return "configuration/devices";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);

}