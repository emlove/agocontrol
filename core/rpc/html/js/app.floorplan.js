/* FloorPlan */

var floorCtrl = null;

App.FloorPlanController = Ember.ArrayController.extend({
    content : [],

    updateDeviceMap : function() {
	var roomMap = [];
	for ( var room in rooms) {
	    roomMap[room] = Ember.Object.create(rooms[room]);
	    roomMap[room].set("devices", []);
	}
	roomMap['none'] = {
	    name : "No Room",
	    devices : []
	};
	for ( var k in deviceMap) {
	    if (deviceMap[k].devicetype == "zwavecontroller") {
		continue;
	    }
	    var rid = deviceMap[k].roomUid === undefined ? "none" : deviceMap[k].roomUid;
	    roomMap[rid].devices.push(deviceMap[k]);
	}

	var _content = Ember.Object.create();

	/* Build the target grid */
	if (this.content.objectAt === undefined || this.content.objectAt(0) === undefined || this.content.objectAt(0).devices === undefined) {
	    var devices = [];
	    for ( var i = 0; i < 3; i++) {
		var sub = [];
		for ( var j = 0; j < 3; j++) {
		    if (j == 0) {
			sub.push(Ember.Object.create({
			    isFirst : true,
			    x : i,
			    y : j,
			    node : {},
			    isDev : false,
			}));
		    } else {
			sub.push(Ember.Object.create({
			    x : i,
			    y : j,
			    node : {},
			    isDev : false,
			}));
		    }
		}
		devices.push(sub);
	    }
	    _content.set("devices", devices);
	} else {
	    var devices = this.content.objectAt(0).devices;
	    for ( var i = 0; i < 3; i++) {
		for ( var j = 0; j < 3; j++) {
		    if (devices[i][j].isDev) {
			var uuid = devices[i][j].get("node").get("uuid");
			devices[i][j].set("node", deviceMap[uuid]);
			devices[i][j].get("node").set("isFirst", j == 0);
			devices[i][j].set("isDev", true);
			_content.set("devices", devices);
		    }
		}
	    }
	    _content.set("devices", this.content.objectAt(0).devices);
	}

	var finalMap = [];
	for ( var room in rooms) {
	    finalMap.push(roomMap[room]);
	}
	finalMap.push(roomMap["none"]);

	_content.set("rooms", finalMap);
	this.set("content", [ _content ]);
    },

    addDevice : function(x, y, uuid) {
	if (this.content.objectAt(0).devices === undefined) {
	    return;
	}

	this.removeDevice(uuid);

	var devices = this.content.objectAt(0).get("devices");

	devices[x][y].set("node", deviceMap[uuid]);
	devices[x][y].set("isDev", true);
	devices[x][y].get("node").set("isFirst", devices[x][y].get("isFirst"));

	var _content = Ember.Object.create();
	_content.set("rooms", this.content.objectAt(0).get("rooms"));
	_content.set("devices", devices);
	this.set("content", [ _content ]);
    },

    removeDevice : function(uuid) {
	var devices = this.content.objectAt(0).get("devices");
	var didRemove = false;
	for ( var i = 0; i < 3; i++) {
	    for ( var j = 0; j < 3; j++) {
		if (devices[i][j].isDev) {
		    var _uuid = devices[i][j].get("node").get("uuid");
		    if (_uuid == uuid) {
			devices[i][j].set("node", Ember.Object.create());
			devices[i][j].get("node").set("isFirst", j == 0);
			devices[i][j].set("isDev", false);
			didRemove = true;
			break;
		    }
		}
	    }
	}

	if (didRemove) {
	    var _content = Ember.Object.create();
	    _content.set("rooms", this.content.objectAt(0).get("rooms"));
	    _content.set("devices", devices);
	    this.set("content", [ _content ]);
	}
    }

});

App.FloorPlanView = Ember.View.extend({
    templateName : "floorplan",
    name : "FloorPlan"
});

App.FloorPlanRoute = Ember.Route.extend({
    model : function() {
	return [];
    },

    setupController : function(controller, model) {
	controller.set('content', model);
	floorCtrl = controller;
	activeController = floorCtrl;
	if (schema != {}) {
	    controller.updateDeviceMap();
	}
    },

    renderTemplate : function() {
	Ember.TEMPLATES['floorplan'] = App.getTemplate("floorplan");
	Ember.TEMPLATES['navigation_floorplan'] = App.getTemplate("navigation/floorplan");
	this.render('navigation_floorplan', {
	    outlet : 'navigation'
	});
	this.render();
    }
});

/* Template helpers */

Ember.Handlebars.registerBoundHelper('placeholder', function(value, options) {
    var tpl = App.helperTemplates["placeholder"];
    if (!tpl) {
	if (App.helperTemplates["placeholder"] === undefined) {
	    App.helperTemplates["placeholder"] = App.getHelperTemplate("devices/placeholder");
	}
	tpl = App.helperTemplates["placeholder"];
    }
    return new Handlebars.SafeString(tpl(value));
});

/* Drag and Drop Javascript helpers */

Ember.Handlebars.registerBoundHelper('enableDnD', function(value, options) {
    Ember.run.next(function() {
	$('.dnd-device').each(function() {
	    $(this).draggable({
		cursor : "move",
		revert : true,
		helper : function(event) {
		    return $('<div style="z-Index: 999; text-align:center; color:#FFF; width: 58px; height: 58px;" class="pretty large primary btn grid-item-icon"></div>');
		}
	    });
	});

	$('.device_tree').droppable({
	    drop : function(event, ui) {
		if (floorCtrl) {
		    var uuid = ui.draggable.data("uuid");
		    floorCtrl.removeDevice(uuid);
		}
	    }
	});
    });
});

Ember.Handlebars.registerBoundHelper('enableDrop', function(value, options) {
    Ember.run.next(function() {
	$('.drop-target').each(function() {
	    $(this).droppable({
		drop : function(event, ui) {
		    if (floorCtrl) {
			var x = $(this).data("x");
			var y = $(this).data("y");
			var uuid = ui.draggable.data("uuid");
			floorCtrl.addDevice(x, y, uuid);
			console.debug("dropped:" + uuid + " on " + x + " / " + y);
		    }
		}
	    });
	});

	$('.device').each(function() {
	    $(this).draggable({
		cursor : "move",
		handle : ".handle",
		revert : true,
		helper : function(event) {
		    return $('<div style="z-Index: 999; text-align:center; color:#FFF;' + 'width: 58px; height: 58px;" class="pretty large primary btn grid-item-icon"></div>');
		}
	    });
	});
    });
});