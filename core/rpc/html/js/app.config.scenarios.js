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
	    content.device = $(this).data('uuid');
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
     * Creates a scenario map out of the form fields inside a container
     */
    this.buildScenarioMap = function(containerID) {
	var map = {};
	var map_idx = 0;
	var commands = document.getElementById(containerID).childNodes;
	for ( var i = 0; i < commands.length; i++) {
	    var command = commands[i];
	    var tmp = {};
	    for ( var j = 0; j < command.childNodes.length; j++) {
		var child = command.childNodes[j];
		if (child.name && child.name == "device" && child.options[child.selectedIndex].value != "sleep") {
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

	return map;
    };

    /**
     * Sends the create scenario command
     */
    this.createScenario = function() {
	if ($("#scenarioName").val() == "") {
	    alert("Please supply an event name!");
	    return;
	}

	var content = {};
	content.command = "setscenario";
	content.uuid = scenarioController;
	content.scenariomap = self.buildScenarioMap("scenarioBuilder");

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
		alert("Please add commands before creating the scenario!");
	    }
	});

    };

    /**
     * Adds a command selection entry
     */
    this.addCommand = function(containerID, defaultValues) {
	var row = document.createElement("div");

	console.log(schema);
	
	if (!containerID) {
	    containerID = "scenarioBuilder";
	}

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
		} else {
		    dspName = dev.name;
		}
		deviceSelect.options[deviceSelect.options.length] = new Option(dspName, dev.uuid);
		deviceSelect.options[deviceSelect.options.length - 1]._dev = dev;
		if (defaultValues && defaultValues.uuid == dev.uuid) {
		    deviceSelect.selectedIndex = deviceSelect.options.length - 1;
		}
	    }
	}

	// Special case for the sleep command
	deviceSelect.options[deviceSelect.options.length] = new Option("Sleep", "sleep");
	deviceSelect.options[deviceSelect.options.length - 1]._dev = "sleep";
	if (defaultValues && !defaultValues.uuid) {
	    deviceSelect.selectedIndex = deviceSelect.options.length - 1;
	}

	row.appendChild(deviceSelect);

	var commandContainer = document.createElement("div");
	commandContainer.style.display = "inline";

	deviceSelect.onchange = function() {
	    commandContainer.innerHTML = "";
	    var dev = deviceSelect.options[deviceSelect.selectedIndex]._dev;
	    var commands = document.createElement("select");
	    commands.name = "command";
	    if (dev != "sleep") {
		for ( var i = 0; i < schema.devicetypes[dev.devicetype].commands.length; i++) {
		    var cmd = schema.devicetypes[dev.devicetype].commands[i];
		    commands.options[i] = new Option(schema.commands[cmd].name, cmd);
		    commands.options[i]._cmd = schema.commands[cmd];
		    if (defaultValues && defaultValues.command == cmd) {
			commands.selectedIndex = i;
		    }
		}
	    } else {
		// Special case for the sleep command
		commands.options[commands.options.length] = new Option("Delay", "scenariosleep");
		commands.options[commands.options.length - 1]._cmd = "sleep";
		if (defaultValues && defaultValues.command == "scenariosleep") {
		    commands.selectedIndex = commands.options.length - 1;
		}
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
			field.setAttribute("size", "15");
			field.setAttribute("name", key);
			field.setAttribute("placeholder", cmd.parameters[key].name);
			if (defaultValues && defaultValues[key]) {
			    field.setAttribute("value", defaultValues[key]);
			}
			commandContainer._params.push(field);
			commandContainer.appendChild(field);
		    }
		} else if (cmd == "sleep") {
		    // Special case for the sleep command
		    commandContainer._params = [];
		    var field = document.createElement("input");
		    field = document.createElement("input");
		    field.setAttribute("type", "text");
		    field.setAttribute("size", "20");
		    field.setAttribute("name", "delay");
		    field.setAttribute("placeholder", "Delay in seconds");
		    if (defaultValues && defaultValues["delay"]) {
			field.setAttribute("value", defaultValues.delay);
		    }
		    commandContainer._params.push(field);
		    commandContainer.appendChild(field);
		}
	    };
	    if (commands.options.length > 0) {
		commands.onchange();
	    }
	};

	deviceSelect.onchange();

	row.appendChild(commandContainer);

	// Mpve up button
	var upBtn = document.createElement("input");
	upBtn.style.display = "inline";
	upBtn.setAttribute("type", "button");
	upBtn.setAttribute("value", "\u21D1");

	upBtn.onclick = function() {
	    var prev = row.previousSibling;
	    document.getElementById(containerID).removeChild(row);
	    document.getElementById(containerID).insertBefore(row, prev);
	};

	row.appendChild(upBtn);

	// Mpve down button
	var downBtn = document.createElement("input");
	downBtn.style.display = "inline";
	downBtn.setAttribute("type", "button");
	downBtn.setAttribute("value", "\u21D3");

	downBtn.onclick = function() {
	    var next = row.nextSibling;
	    document.getElementById(containerID).removeChild(next);
	    document.getElementById(containerID).insertBefore(next, row);
	};

	row.appendChild(downBtn);

	document.getElementById(containerID).appendChild(row);
    };

    this.deleteScenario  = function(item, event) {
	var button_yes = $("#confirmDeleteButtons").data("yes");
	var button_no = $("#confirmDeleteButtons").data("no");
	var buttons = {};
	buttons[button_no] = function() {
	    $("#confirmDelete").dialog("close");
	};
	buttons[button_yes] = function() {
	    self.doDeleteScenario(item, event);
	    $("#confirmDelete").dialog("close");
	};
	$("#confirmDelete").dialog({
	    modal: true,
	    height: 180,
	    width: 500,
	    buttons: buttons
	});
    };
    
    /**
     * Sends the delete scenario command
     */
    this.doDeleteScenario = function(item, event) {
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

    this.editScenario = function(item) {
	var content = {};
	content.scenario = item.uuid;
	content.uuid = scenarioController;
	content.command = 'getscenario';
	sendCommand(content, function(res) {
	    console.log(res);
	    // Build command list
	    for ( var idx in res.result.scenariomap) {
		self.addCommand("scenarioBuilderEdit", res.result.scenariomap[idx]);
	    }

	    // Save the id (needed for the save command)
	    self.openScenario = item.uuid;

	    // Open the dialog
	    if (document.getElementById("editScenarioDialogTitle")) {
	        $("#editScenarioDialog").dialog({
		    title : document.getElementById("editScenarioDialogTitle").innerHTML,
		    modal : true,
		    width : 940,
		    height : 600,
		    close : function() {
		        // Done, restore stuff
		        document.getElementById("scenarioBuilderEdit").innerHTML = "";
		        self.openScenario = null;
		    }
	        });
            }
	});
    };

    this.doEditScenario = function() {
	var content = {};
	content.command = "setscenario";
	content.uuid = scenarioController;
	content.scenario = self.openScenario;
	content.scenariomap = self.buildScenarioMap("scenarioBuilderEdit");
	console.log(content);
	sendCommand(content, function(res) {
	    if (res.result && res.result.scenario) {
		$("#editScenarioDialog").dialog("close");
	    }
	});
    };

    this.runScenario = function(item) {
	var content = {};
	content.uuid = item.uuid;
	content.command = 'on';
	sendCommand(content);
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
