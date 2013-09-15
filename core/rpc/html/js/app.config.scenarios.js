/**
 * Model class
 * 
 * @returns {deviceConfig}
 */
function scenarioConfig() {
    this.devices = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);
    this.scenarios = ko.observableArray([]);

    var self = this;

    this.devices.subscribe(function() {
	var result = self.devices().filter(function(d) {
	    return d.devicetype == "scenario";
	});

	if (result.length == 0) {
	    result = [ {
		name : "dummy",
		uuid : "0"
	    } ];
	}

	self.scenarios(result);
    });

    this.makeEditable = function() {
	var eTable = $("#configTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#configTable").dataTable();
	eTable.$('td.edit_scenario').editable(function(value, settings) {
	    var content = {};
	    content.device = $(this).data('uuid');
	    content.uuid = agoController;
	    content.command = "setdevicename";
	    content.name = value;
	    sendCommand(content);
	    return value;
	}, {
	    data : function(value, settings) {
		return value;
	    },
	    onblur : "cancel"
	});

	eTable.$('td.select_room').editable(function(value, settings) {
	    var content = {};
	    content.device = $(this).parent().data('uuid');
	    content.uuid = agoController;
	    content.command = "setdeviceroom";
	    content.room = value == "unset" ? "" : value;
	    sendCommand(content);
	    return value == "unset" ? "unset" : rooms[value].name;
	}, {
	    data : function(value, settings) {
		var list = {};
		list["unset"] = "--";
		for ( var uuid in rooms) {
		    list[uuid] = rooms[uuid].name;
		}

		return JSON.stringify(list);
	    },
	    type : "select",
	    onblur : "submit"
	});
    };

    this.createScenario = function() {
	alert("TODO");
    };

    this.addCommand = function() {
	var row = document.createElement("div");

	var removeBtn = document.createElement("input");
	removeBtn.style.display = "inline";
	removeBtn.type = "button";
	removeBtn.value = "-";
	row.appendChild(removeBtn);

	removeBtn.onclick = function() {
	    row.parentNode.removeChild(row);
	};

	var deviceSelect = document.createElement("select");
	deviceSelect.name = "device";
	deviceSelect.style.display = "inline";
	deviceSelect.options.length = 0;
	for ( var i = 0; i < self.devices().length; i++) {
	    var dev = self.devices()[i];
	    if (schema.devicetypes[dev.devicetype] && schema.devicetypes[dev.devicetype].commands.length > 0) {
		deviceSelect.options[deviceSelect.options.length] = new Option(dev.name ? dev.name : dev.devicetype, dev.uuid);
		deviceSelect.options[deviceSelect.options.length - 1]._dev = dev;
	    }
	}
	// TODO
	// deviceSelect.options[i++] = new Option("Sleep", "sleep");
	row.appendChild(deviceSelect);

	var commandContainer = document.createElement("div");
	commandContainer.style.display = "inline";

	deviceSelect.onchange = function() {
	    commandContainer.innerHTML = "";
	    var dev = deviceSelect.options[deviceSelect.selectedIndex]._dev;
	    var commands = document.createElement("select");
	    commands.name = "command";
	    for ( var i = 0; i < schema.devicetypes[dev.devicetype].commands.length; i++) {
		var cmd = schema.devicetypes[dev.devicetype].commands[i];
		commands.options[i] = new Option(schema.commands[cmd].name, schema.commands[cmd].name);
		commands.options[i]._cmd = schema.commands[cmd];

	    }
	    commands.style.display = "inline";
	    commandContainer.appendChild(commands);
	    commands.onchange = function() {
		if (commandContainer._params) {
		    for ( var i = 0; i < commandContainer._params.length; i++) {
			try {
			    commandContainer.removeChild(commandContainer._params[i]);

			} catch (e) {
			    // ignore node is gone
			}
		    }
		    commandContainer._params = null;
		}

		var cmd = commands.options[commands.selectedIndex]._cmd;
		if (cmd.parameters) {
		    commandContainer._params = [];
		    for ( var key in cmd.parameters) {
			var field = document.createElement("input");
			field = document.createElement("input");
			field.setAttribute("type", "text");
			field.setAttribute("size", "20");
			field.setAttribute("name", key);
			field.setAttribute("placeholder", cmd.parameters[key].name);
			commandContainer._params.push(field);
			commandContainer.appendChild(field);
		    }
		}
	    };
	    if (commands.options.length > 0) {
		commands.onchange();
	    }
	};

	deviceSelect.onchange();

	row.appendChild(commandContainer);
	document.getElementById("scenarioBuilder").appendChild(row);
    };
}

/**
 * Initalizes the model
 */
function init_scenarioConfig() {
    model = new scenarioConfig();

    model.mainTemplate = function() {
	return "configuration/scenarios";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}