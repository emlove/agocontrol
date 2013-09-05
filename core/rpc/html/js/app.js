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

function getPage() {
    var query = window.location.search.substring(1);
    query = query.split("&")[0];
    return query ? query : "dashboard";
}

var subscription = null;
var url = "/jsonrpc";

var schema = {};
var deviceMap = [];
var rooms = {};
var floorPlans = {};
var systemvar = {};
var currentFloorPlan = ko.observable({});

var supported_devices = [ "switch", "dimmer", "binarysensor", "dimmerrgb", "multilevelsensor", "placeholder" ];

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

function buildfloorPlanList(model) {
    model.floorPlans = ko.observableArray([]);
    for ( var k in floorPlans) {
	model.floorPlans.push({
	    uuid : k,
	    name : floorPlans[k].name
	});
    }
}

/**
 * This gets set when the GUI needs to be initalized after loading the
 * inventory.
 */
var deferredInit = null;

function initGUI() {
    var page = getPage();
    if (page == "dashboard") {
	deferredInit = init_dashBoard;
    } else if (page == "floorplan") {
	deferredInit = init_floorPlan;
    } else if (page == "roomConfig") {
	init_roomConfig();
    } else if (page == "floorplanConfig") {
	init_floorplanConfig();
    } else if (page == "configuration") {
	deferredInit = init_configuration;
    } else if (page == "deviceConfig") {
	init_deviceConfig();
    }
}

initGUI();

// --- AGO --- //

function handleEvent(response) {
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
    systemvar = response.result.system;
    schema = response.result.schema;
    floorPlans = response.result.floorplans;

    /* Parse floorplan uuid */
    var fp = window.location.search.substring(1);
    var tmp = fp.split("&");
    for ( var i = 0; i < tmp.length; i++) {
	if (tmp[i].indexOf("fp=") == 0) {
	    fp = tmp[i].split("=")[1];
	}
    }

    for ( var k in floorPlans) {
	if (k == fp) {
	    var tmp;
	    tmp = floorPlans[k];
	    tmp.uuid = k;
	    currentFloorPlan(tmp);
	}
    }

    console.debug("Inventory:");
    console.debug(response.result);

    var inventory = response.result.inventory;
    for ( var uuid in inventory) {
	if (inventory[uuid].room !== undefined && inventory[uuid].room) {
	    inventory[uuid].roomUID = inventory[uuid].room;
	    if (rooms[inventory[uuid].room] !== undefined) {
		inventory[uuid].room = rooms[inventory[uuid].room].name;
	    } else {
		inventory[uuid].room = "";
	    }

	} else {
	    inventory[uuid].room = "";
	}
	deviceMap.push(new device(inventory[uuid], uuid));
    }

    if (deferredInit) {
	deferredInit();
    }

    if (model.devices !== undefined) {
	model.devices(deviceMap);
    }
    if (model.rooms !== undefined && model.rooms.slice !== undefined) {
	/* get uuid into rooms */
	model.rooms([]);
	for ( var uuid in rooms) {
	    var tmp = rooms[uuid];
	    tmp.uuid = uuid;
	    model.rooms.push(tmp);
	}
    }
    if (model.floorplans !== undefined) {
	/* get uuid into floorplans */
	model.floorplans([]);
	for ( var uuid in floorPlans) {
	    var tmp = floorPlans[uuid];
	    tmp.uuid = uuid;
	    model.floorplans.push(tmp);
	}
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

    $.post(url, JSON.stringify(request), function() {
    }, "json");
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

    $.ajax({
	type : 'POST',
	url : url,
	data : JSON.stringify(request),
	success : function(r) {
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

/* Opens details page for the given device */
function showDetails(device) {
    /* Check if we have a template if yes use it otherwise fall back to default */
    $.ajax({
	type : 'HEAD',
	url : "templates/details/" + device.devicetype + ".html",
	success : function() {
	    doShowDetails(device, device.devicetype);
	},
	error : function() {
	    doShowDetails(device, "default");
	}
    });
}

function doShowDetails(device, template) {
    console.debug(device);
    ko.renderTemplate("details/" + template, device, {}, document.getElementById("detailsPage"));
    $("#detailsPage").dialog({
	title : "Details",
	modal : true,
	width : 650,
	height : 400
    });    
}