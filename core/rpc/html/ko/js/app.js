infuser.defaults.templateUrl = "./templates";

Array.prototype.chunk = function(chunkSize) {
    var array = this;
    return [].concat.apply([], array.map(function(elem, i) {
	return i % chunkSize ? [] : [ array.slice(i, i + chunkSize) ];
    }));
};

ko.bindingHandlers.slider = {
    init : function(element, valueAccessor, allBindingsAccessor) {
	var options = allBindingsAccessor().sliderOptions || {};
	$(element).slider(options);
	ko.utils.registerEventHandler(element, "slidechange", function(event, ui) {
	    var observable = valueAccessor();
	    observable(ui.value);
	});
	ko.utils.domNodeDisposal.addDisposeCallback(element, function() {
	    $(element).slider("destroy");
	});
    },
    update : function(element, valueAccessor) {
	var value = ko.utils.unwrapObservable(valueAccessor());
	if (isNaN(value))
	    value = 0;
	$(element).slider("value", value);
    }
};

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    return query ? query : "dashboard";
}

var subscription = null;
var url = "/jsonrpc";

var schema = {};
var deviceMap = [];
var rooms = {};
var floorPlans = {};

var supported_devices =  ["switch",
                          "dimmer",
                          "binarysensor",
                          "dimmerrgb",
                          "multilevelsensor",
                          "placeholder"];

function device(obj, uuid) {
    var self = this;
    for ( var k in obj) {
	this[k] = obj[k];
    }

    this.uuid = uuid;

    this.handledBy = this['handled-by'];

    var currentState = parseInt(this.state);
    this.state = ko.observable(currentState);

    this.values = ko.observable(this.values);

    if (this.devicetype == "dimmer" || this.devicetype == "dimmerrgb") {
	this.level = ko.observable(currentState);
	this.level.subscribe(function(newValue) {
	    var content = {};
	    content.uuid = uuid;
	    content.command = "setlevel";
	    content.level = newValue;
	    sendCommand(content);
	});
    }

    if (this.devicetype == "dimmerrgb") {
	this.setColor = function() {
	    openColorPicker(uuid);
	};
    }

    if (this.devicetype == "multilevelsensor") {
	this.valueList = ko.computed(function() {
	    var result = [];
	    var i = 0;
	    for ( var k in self.values()) {
		var unit = "-";
		if (schema.units[self.values()[k].unit] !== undefined) {
		    unit = schema.units[self.values()[k].unit].label;
		}
		result.push({
		    name : k.charAt(0).toUpperCase() + k.substr(1),
		    level : self.values()[k].level,
		    unit : unit
		});
		i++;
		if (i == 2) {
		    break;
		}
	    }
	    return result;
	});
    }

    this.turnOn = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'on';
	sendCommand(content);
    };

    this.turnOff = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'off';
	sendCommand(content);
    };

}

var page = getQueryVariable("page");
if (page == "dashboard") {
    init_dashBoard();
} else if (page == "floorPlan") {
    init_floorPlan();
} else if (page == "configuration") {
    init_configuration();
} else if (page == "deviceConfig") {
    init_deviceConfig();
}

// --- AGO --- //

function handleEvent(response) {
    // console.log(response);
    for ( var i = 0; i < deviceMap.length; i++) {
	if (deviceMap[i].uuid == response.result.uuid) {
	    deviceMap[i].state(parseInt(response.result.level));

	    if (response.result.quantity) {
		var values = deviceMap[i].values();
		values[response.result.quantity].level = response.result.level;
		deviceMap[i].values(values);
	    }

	    break;
	}

    }
    getEvent();
}

function getEvent() {
    var request = {};
    request.method = "getevent";
    request.params = {};
    request.params.uuid = subscription;
    request.id = 1;
    request.jsonrpc = "2.0";

    $.post(url, JSON.stringify(request), handleEvent, "json");
}

function handleInventory(response) {
    rooms = response.result.rooms;
    schema = response.result.schema;
    floorPlans = response.result.floorplans;

    console.debug($.isEmptyObject(response.result.floorplans));
    console.debug("Inventory:");
    console.debug(response.result);

    var inventory = response.result.inventory;
    for ( var uuid in inventory) {
	if (inventory[uuid].room !== undefined && inventory[uuid].room) {
	    inventory[uuid].roomUID = inventory[uuid].room;
	    inventory[uuid].room = rooms[inventory[uuid].room].name;

	} else {
	    inventory[uuid].room = "";
	}
	deviceMap.push(new device(inventory[uuid], uuid));
    }

    if (model.devices !== undefined) {
	model.devices(deviceMap);
    }
}

function getInventory() {
    var request = {};
    request.method = "message";
    request.params = {};
    request.params.content = {};
    request.params.content.command = "inventory";
    request.id = 1;
    request.jsonrpc = "2.0";

    $.ajax({
	type : 'POST',
	url : url,
	data : JSON.stringify(request),
	success : handleInventory,
	dataType : "json",
	async : true
    });
}

function unsubscribe() {
    var request = {};
    request.method = "unsubscribe";
    request.id = 1;
    request.jsonrpc = "2.0";
    request.params = {};
    request.params.uuid = subscription;

    $.post(url, JSON.stringify(request), handleUnsubscribe, "json");
}

function handleSubscribe(response) {
    if (response.result) {
	subscription = response.result;
	getInventory();
	getEvent();
	window.onbeforeunload = function(event) {
	    unsubscribe();
	};
    }
}

function sendCommand(content, callback) {
    var request = {};
    request.method = "message";
    request.params = {};
    request.params.content = content;
    request.id = 1;
    request.jsonrpc = "2.0";

    console.log(request);

    $.ajax({
	type : 'POST',
	url : url,
	data : JSON.stringify(request),
	success : function(r) {
	    console.log(r);
	    if (callback !== undefined) {
		callback(r);
	    }
	},
	dataType : "json",
	async : true
    });
}

function subscribe() {
    var request = {};
    request.method = "subscribe";
    request.id = 1;
    request.jsonrpc = "2.0";

    $.post(url, JSON.stringify(request), handleSubscribe, "json");
}

subscribe();

$(function() {
    $("#colorPickerDialog").dialog({
	autoOpen : false,
	modal : true,
	minHeight : 300,
	minWidth : 300,
	buttons : {
	    Cancel : function() {
		$(this).dialog("close");
	    },
	    OK : function() {
		var content = {};
		content.uuid = $("#colorPickerDialog").data('uuid');
		content.command = "setcolor";
		var color = $('#colorValue').val();
		content.red = parseInt(color.substring(0, 2), 16);
		content.green = parseInt(color.substring(2, 4), 16);
		content.blue = parseInt(color.substring(4, 6), 16);
		sendCommand(content);
		$(this).dialog("close");
	    }
	}
    });
});

/* Opens color picker */
function openColorPicker(uuid) {
    $("#colorPickerDialog").data('uuid', uuid);
    $("#colorPickerDialog").dialog("open");
}
