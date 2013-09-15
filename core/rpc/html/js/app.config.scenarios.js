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

    /**
     * Sends the create scenario command
     */
    this.createScenario = function() {
	if ($("#scenarioName").val() == "") {
	    alert("Please supply an event name!");
	    return;
	}

	var map = {};
	var map_idx = 0;
	var commands = document.getElementById("scenarioBuilder").childNodes;
	for ( var i = 0; i < commands.length; i++) {
	    var command = commands[i];
	    var tmp = {};
	    for ( var j = 0; j < command.childNodes.length; j++) {
		var child = command.childNodes[j];
		if (child.name && child.name == "device") {
		    tmp.uuid = child.options[child.selectedIndex].value;
		} else if (child.tagName == "DIV") {
		    for ( var k = 0; k < child.childNodes.length; k++) {
			var subChild = child.childNodes[k];
			if (subChild.name && subChild.name == "command") {
			    tmp.command = subChild.options[subChild.selectedIndex].value;
			}
			if (subChild.name && subChild.type && subChild.type == "text") {
			    tmp[subChild.name] = subChild.value;
			}
		    }
		}
	    }
	    map[map_idx++] = tmp;
	}

	var content = {};
	content.command = "setscenario";
	content.uuid = scenarioController;
	content.scenariomap = map;

	sendCommand(content, function(res) {
	    console.log(res);
	    if (res.result && res.result.scenario) {
		var cnt = {};
		cnt.uuid = agoController;
		cnt.device = res.result.scenario;
		cnt.command = "setdevicename";
		cnt.name = $("#scenarioName").val();
		sendCommand(cnt, function(nameRes) {
		    if (nameRes.result && nameRes.result.returncode == "0") {
			self.scenarios.push({
			    name : cnt.name,
			    uuid : res.result.scenario,
			    room : "",
			});
			document.getElementById("scenarioBuilder").innerHTML = "";
		    }
		});
	    } else {
		alert("ERROR");
	    }
	});

    };

    /**
     * Adds a command selection entry
     */
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
	self.devices.sort(function(a, b) {
	    return a.room.localeCompare(b.room);
	});
	for ( var i = 0; i < self.devices().length; i++) {
	    var dev = self.devices()[i];
	    if (schema.devicetypes[dev.devicetype] && schema.devicetypes[dev.devicetype].commands.length > 0 && dev.name) {
		var dspName = "";
		if (dev.room) {
		    dspName = dev.room + " - " + dev.name;
		}
		else {
		    dspName = dev.name;
		}
		deviceSelect.options[deviceSelect.options.length] = new Option(dspName, dev.uuid);
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
		commands.options[i] = new Option(schema.commands[cmd].name, cmd);
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

    /**
     * Sends the delete scenario command
     */
    this.deleteScenario = function(item, event) {
	$('#configTable').block({
	    message : '<div>Please wait ...</div>',
	    css : {
		border : '3px solid #a00'
	    }
	});
	var content = {};
	content.scenario = item.uuid;
	content.uuid = scenarioController;
	content.command = 'delscenario';
	sendCommand(content, function(res) {
	    if (res.result && res.result.result == 0) {
		self.scenarios.remove(function(e) {
		    return e.uuid == item.uuid;
		});
		$("#configTable").dataTable().fnDeleteRow(event.target.parentNode.parentNode);
		$("#configTable").dataTable().fnDraw();
	    } else {
		alert("Error while deleting scenarios!");
	    }
	    $('#configTable').unblock();
	});
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