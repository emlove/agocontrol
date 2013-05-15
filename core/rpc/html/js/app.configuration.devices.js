/* This is an example of the MVC model */

/* Maintains data gets events from the outside */
App.ConfigurationDevicesController = Ember.ObjectController.extend({
    content : [],

    updateDeviceMap : function() {
	var devs = [];
	for ( var k in deviceMap) {
	    if (deviceMap[k].devicetype == "scenario" || deviceMap[k].devicetype == "event" || deviceMap[k].devicetype == "zwavecontroller") {
		continue;
	    }
	    devs.push(deviceMap[k]);
	}
	this.set("content", devs);
    },

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
