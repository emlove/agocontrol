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
	var value = valueAccessor();
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
var variables = {};
var currentFloorPlan = ko.observable({});

var agoController = null;
var eventController = null;
var dataLoggerController = null;

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

    if (this.devicetype == "dataloggercontroller") {
	dataLoggerController = uuid;
    }

    if (this.devicetype == "agocontroller") {
	agoController = uuid;
    }

    if (this.devicetype == "eventcontroller") {
	eventController = uuid;
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
    } else if (page == "variablesConfig") {
	init_variablesConfig();
    } else if (page == "floorplanConfig") {
	init_floorplanConfig();
    } else if (page == "configuration") {
	deferredInit = init_configuration;
    } else if (page == "deviceConfig") {
	init_deviceConfig();
    } else if (page == "systemConfig") {
	deferredInit = init_systemConfig;
    } else if (page == "eventConfig") {
	init_eventConfig();
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
		if (values[response.result.quantity] === undefined) {
		    console.log("BROKEN DEVICE [" + response.result.uuid + "]");
		    break;
		}
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
    variables = response.result.variables;

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

    if (model.variables !== undefined) {
	model.variables([]);
	for ( var key in variables) {
	    var tmp = {};
	    tmp.variable = key;
	    tmp.value = variables[key];
	    model.variables.push(tmp);
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

function sendCommand(content, callback, timeout) {
    var request = {};
    request.method = "message";
    request.params = {};
    request.params.content = content;
    if (timeout) {
	request.params.replytimeout = timeout;
    }
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

/**
 * Opens details page for the given device
 * 
 * @param device
 * @param environment
 */
function showDetails(device, environment) {
    /* Check if we have a template if yes use it otherwise fall back to default */
    $.ajax({
	type : 'HEAD',
	url : "templates/details/" + device.devicetype + ".html",
	success : function() {
	    doShowDetails(device, device.devicetype, environment);
	},
	error : function() {
	    doShowDetails(device, "default");
	}
    });
}

/**
 * Formats a date object
 * 
 * @param date
 * @param simple
 * @returns {String}
 */
function formatDate(date) {
    var hour = date.getHours() < 10 ? "0" + date.getHours() : date.getHours();
    var min = date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes();
    var day = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
    var month = date.getMonth() + 1;
    month = month < 10 ? "0" + month : month;

    return date.getFullYear() + "." + month + "." + day + " " + hour + ":" + min;
};

/**
 * Shows the detail page of a device
 * 
 * @param device
 * @param template
 * @param environment
 */
function doShowDetails(device, template, environment) {
    ko.renderTemplate("details/" + template, device, {
	afterRender : function() {
	    var dialogWidth = 800;
	    var dialogHeight = 300;

	    if (document.getElementById('graph')) {
		$('#graph').block({
		    message : '<div>Please wait ...</div>',
		    css : {
			border : '3px solid #a00'
		    }
		});

		/* Setup start date */
		var start = new Date((new Date()).getTime() - 24 * 3600 * 1000);
		$("#start_date").datepicker({
		    dateFormat : "dd.mm.yy",
		    onSelect : function() {
			renderGraph(device, document.getElementById('graph')._environment);
		    }
		});
		$("#start_date").datepicker("setDate", start);

		/* Setup end date */
		$("#end_date").datepicker({
		    dateFormat : "dd.mm.yy",
		    onSelect : function() {
			renderGraph(device, document.getElementById('graph')._environment);
		    }
		});
		$("#end_date").datepicker("setDate", new Date());

		renderGraph(device, environment ? environment : device.valueList()[0].name);
		dialogWidth = 1000;
		dialogHeight = 720;
	    }

	    $("#detailsPage").dialog({
		title : "Details",
		modal : true,
		width : dialogWidth,
		height : dialogHeight,
		close : function() {
		    var graphContainer = document.getElementById('graph');
		    if (graphContainer) {
			graphContainer.parentNode.removeChild(graphContainer);
		    }
		}
	    });

	}
    }, document.getElementById("detailsPage"));
}

/**
 * Renders the graph for the given device and environment
 * 
 * @param device
 * @param environment
 */
function renderGraph(device, environment) {
    var max_ticks = 25; // User option?

    var endDate = new Date($("#end_date").datepicker("getDate").getTime() + 1000 * 3600 * 23 + 60 * 59);

    var content = {};
    content.uuid = dataLoggerController;
    content.command = "getloggergraph";
    content.deviceid = device.uuid;
    content.start = $("#start_date").datepicker("getDate").toString();
    content.end = endDate.toString();
    content.env = environment.toLowerCase();

    sendCommand(content, function(res) {
	if (!res.result || !res.result.result || !res.result.result.values) {
	    alert("Error while loading Graph!");
	    $('#graph').unblock();
	    return;
	}

	/* Prepare the data */
	var data = [];
	var values = res.result.result.values;

	/* Split the values into buckets */
	var num_buckets = Math.max(1, Math.floor(values.length / max_ticks));
	var buckets = values.chunk(num_buckets);
	var labels = [];
	var i = 0;

	/*
	 * Compute averange for each bucket and pick a representative time to
	 * display
	 */
	for ( var j = 0; j < buckets.length; j++) {
	    var bucket = buckets[j];
	    var ts = bucket[0].time + (bucket[bucket.length - 1].time - bucket[0].time) / 2;
	    labels.push(new Date(Math.floor(ts) * 1000));
	    var value = 0;
	    for ( var k = 0; k < bucket.length; k++) {
		value += bucket[k].level;
	    }
	    data.push([ i, value / k ]);
	    i++;
	}

	/* Get the unit */
	var unit = "";
	for ( var k = 0; k < device.valueList().length; k++) {
	    if (device.valueList()[k].name == environment) {
		unit = device.valueList()[k].unit;
		break;
	    }
	}

	/* Render the graph */
	var container = document.getElementById('graph');
	container._environment = environment;
	Flotr.draw(container, [ data ], {
	    HtmlText : false,
	    title : environment,
	    mode : "time",
	    yaxis : {
		tickFormatter : function(x) {
		    return x + " " + unit;
		},
	    },
	    mouse : {
		track : true,
		relative : true,

		trackFormatter : function(o) {
		    return formatDate(labels[Math.round(o.x)]) + " - " + o.y + " " + unit;
		}
	    },
	    xaxis : {
		noTicks : i,
		labelsAngle : 90,
		tickDecimals : 0,
		tickFormatter : function(x) {
		    return formatDate(labels[x]);
		}
	    }
	});

	/* We have no data ... */
	if (data.length == 0) {
	    var canvas = document.getElementsByClassName("flotr-overlay")[0];
	    var context = canvas.getContext("2d");
	    var x = canvas.width / 2;
	    var y = canvas.height / 2;

	    context.font = "30pt Arial";
	    context.textAlign = "center";
	    context.fillStyle = "red";
	    context.fillText('No data found for given time frame!', x, y);
	}

	$('#graph').unblock();
    }, 5);
}