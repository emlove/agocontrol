/* AgoControl */

Array.prototype.chunk = function(chunkSize) {
    var array = this;
    return [].concat.apply([], array.map(function(elem, i) {
	return i % chunkSize ? [] : [ array.slice(i, i + chunkSize) ];
    }));
};

var subscription = null;
var url = "/jsonrpc";

var schema = {};
var deviceMap = {};
Device = Ember.Object.extend({});

function handleEvent(response) {
    if (response.result) {
	console.log(response.result);
	deviceMap[response.result.uuid].set('state', parseInt(response.result.level));
	if (response.result.quantity) {
	    var values = deviceMap[response.result.uuid].values;
	    values[response.result.quantity].level = response.result.level;
	    deviceMap[response.result.uuid].set('values', values);
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
    var rooms = response.result.rooms;
    schema = response.result.schema;
    console.log(response.result);
    for ( var uuid in response.result.inventory) {
	deviceMap[uuid] = Device.create(response.result.inventory[uuid]);
	deviceMap[uuid].uuid = uuid;
	deviceMap[uuid].state = parseInt(deviceMap[uuid].state);
	if (deviceMap[uuid].room !== undefined && rooms[deviceMap[uuid].room] !== undefined) {
	    deviceMap[uuid].room = rooms[deviceMap[uuid].room].name;
	}
	for ( var key in response.result.inventory[uuid]) {
	    deviceMap[uuid].addObserver(key, deviceMap[uuid], function(k) {
		return function() {
		    if (indexCtrl) {
			indexCtrl.updateDeviceMap();
		    }
		};
	    }(key));
	}

	if (indexCtrl) {
	    indexCtrl.updateDeviceMap();
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

function handleSubscribe(response) {
    if (response.result) {
	subscription = response.result;
	getInventory();
	getEvent();
    }
}

function sendCommand(content) {
    var request = {};
    request.method = "message";
    request.params = {};
    request.params.content = content;
    request.params.content;
    request.id = 1;
    request.jsonrpc = "2.0";

    $.ajax({
	type : 'POST',
	url : url,
	data : JSON.stringify(request),
	success : function(r) {
	    console.log(r);
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

/* EmberJS Application */

var App = Ember.Application.create({
    ApplicationController : Ember.Controller.extend(),
    ready : function() {
	subscribe();
    },

    getTemplate : function(name) {
	var template = '';
	$.ajax({
	    url : './templates/' + name + '.html?' + (new Date()).getTime(),
	    async : false,
	    success : function(text) {
		template = text;
	    }
	});

	return Ember.Handlebars.compile(template);
    },

    getHelperTemplate : function(name) {
	var template = " ";
	$.ajax({
	    url : './templates/' + name + '.html?' + (new Date()).getTime(),
	    async : false,
	    success : function(text) {
		template = text;
	    }
	});

	if (template == " ") {
	    return false;
	}

	return Handlebars.compile(template);
    },

});

App.helperTemplates = {};

App.Router.map(function() {
    // put your routes here
});

/* Template helpers */

Ember.Handlebars.registerBoundHelper('device', function(value, options) {
    var tpl = null;
    if (App.helperTemplates[value.devicetype] === undefined) {
	App.helperTemplates[value.devicetype] = App.getHelperTemplate("devices/" + value.devicetype);
    }

    tpl = App.helperTemplates[value.devicetype];
    if (!tpl) {
	if (App.helperTemplates["empty"] === undefined) {
	    App.helperTemplates["empty"] = App.getHelperTemplate("devices/empty");
	}
	tpl = App.helperTemplates["empty"];
    }

    // Build value list
    if (value.values !== undefined) {
	if (App.helperTemplates["value"] === undefined) {
	    App.helperTemplates["value"] = App.getHelperTemplate("devices/value");
	}
	var subTpl = App.helperTemplates["value"];

	value.valueList = "";
	var i = 0;
	for ( var k in value.values) {
	    // We have no room for more then two
	    if (i == 2) {
		break;
	    }

	    var tmp = value.values[k];
	    // Capitalize the first letter of the name
	    tmp.name = k.charAt(0).toUpperCase() + k.slice(1);

	    // Query the unit's label from the schema
	    if (schema.units[tmp.unit] !== undefined) {
		tmp.unit = schema.units[tmp.unit].label;
	    }
	    value.valueList += subTpl(tmp);
	    i++;
	}
	value.valueList = new Handlebars.SafeString(value.valueList);
    }

    return new Handlebars.SafeString(tpl(value));
});

/* Used to setUp buttons and sliders */
Ember.Handlebars.registerBoundHelper('doSetup', function(value, options) {

    $(".slider").each(function() {
	$(this).empty().slider({
	    value : $(this).data('value'),
	    min : 0,
	    max : 100,
	    step : 5,
	    disabled : $(this).data('value') == "-",
	    stop : function(event, ui) {
		var content = {};
		content.uuid = $(this).data('uuid');
		content.command = "setlevel";
		content.level = ui.value;
		sendCommand(content);
	    }
	});
    });

    $('.cmd-btn').each(function() {
	$(this).click(function() {
	    var content = {};
	    content.uuid = $(this).data('uuid');
	    content.command = $(this).data('value');
	    sendCommand(content);
	});
    });
});

/* Index - Devices View */

var indexCtrl = null;

App.IndexController = Ember.ObjectController.extend({
    content : [],

    updateDeviceMap : function() {
	var devs = [];
	for ( var k in deviceMap) {
	    if (deviceMap[k].devicetype == "scenario" || deviceMap[k].devicetype == "event" || deviceMap[k].devicetype == "zwavecontroller") {
		continue;
	    }
	    devs.push(deviceMap[k]);
	}
	devs = devs.chunk(3);
	for ( var i = 0; i < devs.length; i++) {
	    devs[i][0].isFirst = true;
	}
	this.set("content", devs);
    },

});

App.IndexView = Ember.View.extend({
    templateName : "index",
    name : "index"
});

App.IndexRoute = Ember.Route.extend({
    model : function() {
	return [];
    },

    setupController : function(controller, model) {
	controller.set('content', model);
	indexCtrl = controller;
    },

    renderTemplate : function() {
	Ember.TEMPLATES['index'] = App.getTemplate("devices");
	this.render();
    },
});
