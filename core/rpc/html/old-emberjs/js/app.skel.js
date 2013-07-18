/* This is an example of the MVC model */

/* Maintains data gets events from the outside */
App.SkelController = Ember.ObjectController.extend({
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
App.SkelView = Ember.View.extend({
    templateName : "skel",
    name : "skel"
});

/* Route - glues view and controller */
App.SkelRoute = Ember.Route.extend({
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
	Ember.TEMPLATES['skel'] = App.getTemplate("skel");
	this.render('none', {
	    outlet : 'navigation'
	});
	this.render();
    }
});