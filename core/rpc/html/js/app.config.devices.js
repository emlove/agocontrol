/**
 * Model class
 * 
 * @returns {deviceConfig}
 */
function deviceConfig() {
    var self = this;
    this.devices = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);

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

	var resetFilter = function() {
	    var oSettings = eTable.fnSettings();
	    for ( var i = 0; i < oSettings.aoPreSearchCols.length; i++) {
		oSettings.aoPreSearchCols[i].sSearch = "";
	    }
	    oSettings.oPreviousSearch.sSearch = "";
	    eTable.fnDraw();
	};

	var baseWeight = 15;
	var tagMap = {};
	for ( var i = 0; i < self.devices().length; i++) {
	    var dev = self.devices()[i];
	    if (tagMap["type_" + dev.devicetype]) {
		tagMap["type_" + dev.devicetype].w++;
	    } else {
		tagMap["type_" + dev.devicetype] = {
		    type : "device",
		    value : dev.devicetype,
		    w : baseWeight,
		};
	    }
	    if (dev.room) {
		if (tagMap["room_" + dev.room]) {
		    tagMap["room_" + dev.room].w++;
		} else {
		    tagMap["room_" + dev.room] = {
			type : "room",
			value : dev.room,
			w : baseWeight,
		    };
		}
	    }
	}

	document.getElementById("tags").innerHTML = "";
	var list = document.createElement("ul");
	document.getElementById("tags").appendChild(list);

	for ( var k in tagMap) {
	    var obj = tagMap[k];
	    var item = document.createElement("li");
	    var link = document.createElement("a");
	    link.href = "#";
	    link.setAttribute("data-weight", obj.w);
	    link.appendChild(document.createTextNode(obj.value));
	    item.appendChild(link);
	    list.appendChild(item);

	    link.onclick = function(value, idx) {
		return function() {
		    resetFilter();
		    eTable.fnFilter(value, idx);
		    return false;
		};
	    }(obj.value, obj.type == "device" ? 2 : 1);

	}

	// All link for reset
	var item = document.createElement("li");
	var link = document.createElement("a");
	link.href = "#";
	link.setAttribute("data-weight", baseWeight + self.devices().length);
	link.appendChild(document.createTextNode("All"));
	item.appendChild(link);
	list.appendChild(item);

	link.onclick = function() {
	    resetFilter();
	    return false;
	};

	$('#tagArea').tagcanvas({
	    textColour : '#ff0000',
	    outlineColour : '#0000ff',
	    reverse : true,
	    depth : 0.8,
	    maxSpeed : 0.05,
	    weight : true,
	    weightFrom : "data-weight",
	    zoom : 1.5,
	}, "tags");

    };
}

/**
 * Initalizes the model
 */
function init_deviceConfig() {
    model = new deviceConfig();

    model.mainTemplate = function() {
	return "configuration/devices";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}