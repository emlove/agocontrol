/* Maintains data gets events from the outside */
App.ConfigurationDevicesController = Ember.ArrayController.extend({
    content : [],

    updateDeviceMap : function() {
	if (this.content.length > 0) {
	    return;
	}

	var devs = [];
	for ( var k in deviceMap) {
	    if (deviceMap[k].devicetype == "scenario" || deviceMap[k].devicetype == "event" || deviceMap[k].devicetype == "zwavecontroller") {
		continue;
	    }
	    devs.push(deviceMap[k]);
	}
	this.set("content", devs);
    }
});

/* View */
App.ConfigurationDevicesView = Ember.View.extend({
    templateName : "configurationdevices",
    name : "ConfigurationDevices"
});

/* Route - glues view and controller */
App.ConfigurationDevicesRoute = Ember.Route.extend({
    model : function() {
	return [];
    },

    setupController : function(controller, model) {
	controller.set('content', model);
	activeController = controller;
	if (schema != {}) {
	    controller.updateDeviceMap();
	}
    },

    renderTemplate : function() {
	Ember.TEMPLATES['configurationdevices'] = App.getTemplate("configuration/devices");
	Ember.TEMPLATES['navigation_configuration'] = App.getTemplate("navigation/configuration");
	this.render('navigation_configuration', {
	    outlet : 'navigation'
	});
	this.render();
    }
});

/* Make table editable */

Ember.Handlebars.registerBoundHelper('makeTableEditable', function(value, options) {
    Ember.run.next(function() {
	var eTable = $("#configTable").dataTable();
	eTable.$('td.edit_device').editable(function(value, settings) {
	    alert("TODO: DO UPDATE!");
	}, {
	    data : function(value, settings) {
		return $(value).text();
	    },
	    onblur : "cancel"
	});

	eTable.$('td.select_device_room').editable(function(value, settings) {
	    alert("TODO: DO UPDATE!");
	}, {
	    data : function(value, settings) {
		var list = {};
		for ( var uuid in rooms) {
		    list[uuid] = rooms[uuid].name;
		}
		;
		return JSON.stringify(list);
	    },
	    type : "select",
	    onblur : "cancel"
	});
    });
});
