/* Index - Devices View */

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
	    for ( var j = 1; j < devs[i].length; j++) {
		devs[i][j].isFirst = false;
	    }
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
	activeController = controller;
	if (schema != {}) {
	    controller.updateDeviceMap();
	}
    },

    renderTemplate : function() {
	Ember.TEMPLATES['index'] = App.getTemplate("devices");
	Ember.TEMPLATES['navigation_default'] = App.getTemplate("navigation/default");
	this.render('navigation_default', {
	    outlet : 'navigation'
	});
	this.render();
    }
});
