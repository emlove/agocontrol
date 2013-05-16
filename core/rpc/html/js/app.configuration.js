/* This is an example of the MVC model */

/* Maintains data gets events from the outside */
App.ConfigurationController = Ember.ObjectController.extend({
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
App.ConfigurationView = Ember.View.extend({
    templateName : "configuration",
    name : "configuration"
});

/* Route - glues view and controller */
App.ConfigurationRoute = Ember.Route.extend({
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
	Ember.TEMPLATES['configuration'] = App.getTemplate("configuration");
	Ember.TEMPLATES['navigation_configuration'] = App.getTemplate("navigation/configuration");
	this.render('navigation_configuration', {
	    outlet : 'navigation'
	});
	this.render();
    }
});

/* Tab nav helper */
Ember.Handlebars.registerBoundHelper('enableTabNav', function(value, options) {
    Ember.run.next(function() {
	$('.tab-nav li > a').click(function() {
	    $(".tab-nav li").each(function() {
		$(this).removeClass('active');
	    });

	    $(this).parent().toggleClass('active');

	    this.$el = $('.tabs');
	    var index = $(this).parent().index();
	    this.$content = this.$el.find(".tab-content");
	    this.$nav = $(this).parent().find('li');
	    this.$nav.add(this.$content).removeClass("active");
	    this.$nav.eq(index).add(this.$content.eq(index)).addClass("active");
	});

    });
});
