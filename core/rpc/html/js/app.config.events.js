/* Event generation code */

/**
 * Model class
 * 
 * @returns
 */
function eventConfig() {
    this.hasNavigation = ko.observable(true);

    this.current_id = 0;

    this.eventMap = schema.events;
    this.deviceList = deviceMap;

    var self = this;

    this.createEvent = function() {
	alert("NOT DONE YET!");
    };

    /**
     * Adds a nested element
     */
    this.addNesting = function(container, type) {
	var dl = document.createElement("dl");
	var dd = document.createElement("dd");
	dl.setAttribute("class", "operator");

	var subList = document.createElement("dl");
	subList.setAttribute("class", "subList");

	dl.appendChild(dd);
	dd.appendChild(document.createTextNode("Operator: "));

	var radio = document.createElement("input");
	radio.name = "op_" + (self.current_id);
	radio.id = radio.name + "_and";
	radio.type = "radio";
	radio.value = "and";
	radio.checked = (type == "and");
	var label = document.createElement("label");
	label.appendChild(document.createTextNode("and"));
	label.setAttribute("for", radio.id);
	dd.appendChild(radio);
	dd.appendChild(label);

	var radio = document.createElement("input");
	radio.name = "op_" + (self.current_id);
	radio.id = radio.name + "_or";
	radio.type = "radio";
	radio.value = "or";
	radio.checked = (type == "or");
	var label = document.createElement("label");
	label.appendChild(document.createTextNode("or"));
	label.setAttribute("for", radio.name);
	dd.appendChild(radio);
	dd.appendChild(label);

	self.current_id++;

	var adSbutton = document.createElement("button");
	adSbutton.appendChild(document.createTextNode("Add criteria"));
	adSbutton._list = subList;
	adSbutton.onclick = function() {
	    self.addSegment(this._list);
	};

	dd.appendChild(adSbutton);

	var adNbutton = document.createElement("button");
	adNbutton.appendChild(document.createTextNode("Add nesting"));
	adNbutton._list = dl;
	adNbutton.onclick = function() {
	    self.addNesting(this._list.lastChild, "and");
	};

	dd.appendChild(adNbutton);

	var button = document.createElement("button");
	button.appendChild(document.createTextNode("delete"));
	button._list = dl;
	button.onclick = function() {
	    if (this._list.parentNode == document.getElementById("eventBuilder") && document.getElementsByClassName("operator").length == 1) {
		alert("Last element cannot be deleted!");
		return;
	    }
	    this._list.parentNode.removeChild(this._list);
	};

	dd.appendChild(button);

	var button = document.createElement("button");
	button.appendChild(document.createTextNode("<"));
	button._list = dl;
	button.onclick = function() {
	    if (this._list.parentNode == document.getElementById("eventBuilder")) {
		alert("This is already a top level element!");
		return;
	    }
	    var parentElem = dl.parentNode;
	    var newParent = dl.parentNode.parentNode.parentNode;
	    parentElem.removeChild(dl);
	    if (parentElem.nextSibling) {
		newParent.insertBefore(dl, parentElem.nextSibling);
	    } else {
		newParent.appendChild(dl);
	    }
	};

	dd.appendChild(button);

	var button = document.createElement("button");
	button.appendChild(document.createTextNode(">"));
	button._list = dl;
	button.onclick = function() {
	    var ops = document.getElementsByClassName("operator");
	    if (ops.length == 1) {
		alert("This is already a top level element!");
		return;
	    } else {
		var parentElem = dl.parentNode;
		var newParent = dl;
		while ((newParent = newParent.previousSibling) != null) {
		    if (newParent.nodeType == 1) {
			break;
		    }
		}

		if (newParent.className != "operator") {
		    alert("Item is already at the maximum indent level!");
		    return;
		}
		parentElem.removeChild(dl);
		newParent.lastChild.appendChild(dl);
	    }

	};

	dd.appendChild(button);

	var tmp = document.createElement("dd");
	tmp.appendChild(subList);
	dl.appendChild(tmp);

	container.appendChild(dl);

	return [ dl, subList ];
    };

    /**
     * Adds a new segment
     */
    this.addSegment = function(container, eventObj) {
	var dd = document.createElement("dd");

	var span = document.createElement("span");
	span.className = "eventParams";

	dd.appendChild(span);

	if (eventObj) {
	    self.renderEvent(eventObj.path, self.eventMap[eventObj.path], span, eventObj);
	} else {
	    var selector = document.getElementById("eventSelector");
	    self.renderEvent(selector.options[selector.selectedIndex].value, self.eventMap[selector.options[selector.selectedIndex].value], span);
	}

	var button = document.createElement("button");
	button.appendChild(document.createTextNode("delete"));
	button._listItem = dd;
	button.onclick = function() {
	    this._listItem.parentNode.removeChild(this._listItem);
	};
	dd.appendChild(button);
	container.appendChild(dd);
    };

    /**
     * Converts one operation to JSON
     */
    this.operationToJSON = function(tmp) {
	var op = {};
	op.sub = [];
	var radios = tmp.firstChild.getElementsByTagName("input");
	for ( var j = 0; j < radios.length; j++) {
	    if (radios[j].checked) {
		op.type = radios[j].value;
	    }
	}

	if (tmp.getElementsByClassName("subList").length > 0) {
	    var subList = tmp.getElementsByClassName("subList")[0];
	    for ( var j = 0; j < subList.childNodes.length; j++) {
		var eventObj = {};
		var selects = subList.childNodes[j].getElementsByTagName("select");
		var selector = document.getElementById("eventSelector");
		eventObj.path = selector.options[selector.selectedIndex].value;

		if (selects.length > 0) {
		    eventObj.comp = selects[1].options[selects[1].selectedIndex].value;
		    eventObj.param = selects[0].options[selects[0].selectedIndex].value;
		    eventObj.value = subList.childNodes[j].getElementsByTagName("input")[0].value;
		}
		op.sub.push(eventObj);
	    }

	    var subOps = subList.parentNode.childNodes;
	    for ( var j = 0; j < subOps.length; j++) {
		if (subOps[j].className == "operator") {
		    op.sub.push(self.operationToJSON(subOps[j]));
		}
	    }
	}

	return op;
    };

    /**
     * Create ajson structure out of the whole event
     */
    this.createJSON = function(uuid) {
	var ops = document.getElementsByClassName("operator");
	var res = [];
	for ( var i = 0; i < ops.length; i++) {
	    if (ops[i].parentNode != document.getElementById("eventBuilder")) {
		continue;
	    }
	    res.push(self.operationToJSON(ops[i]));
	}
	var eventSelector = document.getElementById("eventSelector");
	res = {
	    "conn" : document.getElementById("conn_and").checked ? "and" : "or",
	    "elements" : res,
	    "path" : eventSelector.options[eventSelector.selectedIndex].value
	};

	var action = {};
	action.command = document.getElementById("commandSelect").options[document.getElementById("commandSelect").selectedIndex].value;
	action.uuid = self.deviceList[document.getElementById("deviceListSelect").options[document.getElementById("deviceListSelect").selectedIndex].value].id;

	var event_name = document.getElementById("event_name").value;
	console.log(res);
	console.log(event_name);
    };

    /**
     * Creates a new operation
     */
    this.createOperation = function(sub, container, type) {
	var res = self.addNesting(container, type);
	var dl = res[0];
	var subList = res[1];
	for ( var i = 0; i < sub.length; i++) {
	    if (sub[i].type) {
		self.createOperation(sub[i].sub, dl.lastChild, sub[i].type);
	    } else {
		self.addSegment(subList, sub[i]);
	    }
	}
    };

    /**
     * (re) Builds the list from JSON
     */
    this.buildListFromJSON = function(str, container) {
	var input = JSON.parse(str);

	document.getElementById("eventBuilder").innerHTML = "";
	var eventSelector = getEventSelector(self.eventMap, document.getElementById("eventBuilder"));
	eventSelector.id = "eventSelector";
	document.getElementById("eventBuilder").appendChild(eventSelector);
	self.renderMainConnector(input.conn, document.getElementById("eventBuilder"));

	var inputList = input.elements;
	for ( var i = 0; i < inputList.length; i++) {
	    var op = inputList[i];
	    self.createOperation(op.sub, document.getElementById("eventBuilder"), op.type);
	}

	var eventSelector = document.getElementById("eventSelector");
	for ( var i = 0; i < eventSelector.options.length; i++) {
	    if (eventSelector.options[i].value == input.path) {
		eventSelector.options[i].selected = true;
		break;
	    }
	}
    };

    /**
     * Creates the event selector
     */
    this.getEventSelector = function(events, container, defaultPath) {
	var eventList = document.createElement("select");
	eventList.onchange = function() {
	    var path = eventList.options[eventList.selectedIndex].value;
	    var eventParams = document.getElementsByClassName("eventParams");
	    for ( var i = 0; i < eventParams.length; i++) {
		self.renderEvent(path, events[path], eventParams[i]);
	    }
	};
	var i = 0;
	for (path in events) {
	    var opt = new Option(events[path].description, path);
	    eventList.options[i] = opt;
	    if (defaultPath && defaultPath == path) {
		eventList.options[i].selected = true;
	    }
	    i++;
	}

	return eventList;
    };

    /**
     * Renders the main content
     */
    this.renderMainConnector = function(type, container) {
	var radio = document.createElement("input");
	radio.name = "conn";
	radio.id = radio.name + "_and";
	radio.type = "radio";
	radio.value = "and";
	radio.checked = (type == "and");
	var label = document.createElement("label");
	label.appendChild(document.createTextNode("and"));
	label.setAttribute("for", radio.id);
	container.appendChild(radio);
	container.appendChild(label);

	var radio = document.createElement("input");
	radio.name = "conn";
	radio.id = radio.name + "_or";
	radio.type = "radio";
	radio.value = "or";
	radio.checked = (type == "or");
	var label = document.createElement("label");
	label.appendChild(document.createTextNode("or"));
	label.setAttribute("for", radio.name);

	container.appendChild(radio);
	container.appendChild(label);
    };

    /**
     * Renders an event
     */
    this.renderEvent = function(path, event, container, defaultValues) {
	container.innerHTML = "";

	var params = document.createElement("select");
	params.name = path + ".param";
	if (event.parameters !== undefined) {
	    for ( var i = 0; i < event.parameters.length; i++) {
		var opt = new Option(event.parameters[i], event.parameters[i]);
		params.options[i] = opt;
		if (defaultValues && event.parameters[i] == defaultValues.param) {
		    params.options[i].selected = true;
		}
	    }

	    var comp = document.createElement("select");
	    comp.name = path + ".comp";
	    comp.options[0] = new Option("=", "eq");
	    comp.options[1] = new Option("!=", "new");
	    comp.options[2] = new Option(">", "gt");
	    comp.options[3] = new Option("<", "lt");

	    if (defaultValues) {
		for ( var i = 0; comp.options.length; i++) {
		    if (comp.options[i].value == defaultValues.comp) {
			comp.options[i].selected = true;
			break;
		    }
		}
	    }

	    var inputField = document.createElement("input");
	    inputField.name = path + ".value";
	    if (defaultValues) {
		inputField.value = defaultValues.value;
	    }

	    container.appendChild(params);
	    container.appendChild(comp);
	    container.appendChild(inputField);
	}
    };

    /**
     * Creates the action builder
     */
    this.createActionBuilder = function(container, defaults) {
	var deviceListSelect = document.createElement("select");
	deviceListSelect.id = "deviceListSelect";
	var commandSelect = document.createElement("select");
	commandSelect.id = "commandSelect";
	var commandParams = document.createElement("fieldset");
	var j = 0;
	for ( var i = 0; i < self.deviceList.length; i++) {
	    var dev = self.deviceList[i];
	    if (schema.devicetypes[dev.devicetype] === undefined || schema.devicetypes[dev.devicetype].commands.length == 0) {
		continue;
	    }
	    deviceListSelect.options[j] = new Option(dev["name"] == "" ? dev["id"] : dev["name"], i);
	    if (defaults && defaults.uuid == dev["id"]) {
		deviceListSelect.options[j].selected = true;
	    }
	    j++;
	}

	container.appendChild(deviceListSelect);
	container.appendChild(commandSelect);
	container.appendChild(commandParams);

	deviceListSelect.onchange = function() {
	    if (deviceListSelect.options[deviceListSelect.selectedIndex] == undefined) {
		return;
	    }
	    var idx = deviceListSelect.options[deviceListSelect.selectedIndex].value;
	    self.createCommandSelector(commandSelect, commandParams, self.deviceList[idx].devicetype);
	};
	if (!defaults) {
	    deviceListSelect.onchange();
	} else {
	    var idx = deviceListSelect.options[deviceListSelect.selectedIndex].value;
	    self.createCommandSelector(commandSelect, commandParams, self.deviceList[idx].devicetype, defaults);
	}
    };

    /**
     * Creates the command selector
     */
    this.createCommandSelector = function(commandSelect, commandParams, type, defaults) {
	commandSelect.options.length = 0;
	for ( var i = 0; i < schema.devicetypes[type].commands.length; i++) {
	    commandSelect.options[i] = new Option(schema.commands[schema.devicetypes[type].commands[i]].name, schema.devicetypes[type].commands[i]);
	    if (defaults && defaults.command == schema.devicetypes[type].commands[i]) {
		commandSelect.options[i].selected = true;
	    }
	}

	commandSelect.onchange = function() {
	    var cmd = schema.commands[commandSelect.options[commandSelect.selectedIndex].value];
	    commandParams.innerHTML = "";
	    if (cmd.parameters !== undefined) {
		commandParams.style.display = "";
		var legend = document.createElement("legend");
		legend.style.fontWeight = 700;
		legend.appendChild(document.createTextNode("Parameters"));
		commandParams.appendChild(legend);
		for ( var param in cmd.parameters) {
		    var label = document.createElement("label");
		    label.appendChild(document.createTextNode(cmd.parameters[param].name + ": "));
		    label.setAttribute("for", cmd.parameters[param].name);
		    commandParams.appendChild(label);

		    var input = document.createElement("input");
		    input.name = cmd.parameters[param].name;
		    input.id = cmd.parameters[param].name;
		    input.className = "cmdParam";
		    commandParams.appendChild(input);

		    var br = document.createElement("br");
		    commandParams.appendChild(br);
		}
	    } else {
		commandParams.style.display = "none";
	    }
	};

	commandSelect.onchange();
    };

    /**
     * Custom binding to init the rendering
     */
    ko.bindingHandlers.initEvents = {
	init : function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext) {
	    var eventSelector = self.getEventSelector(self.eventMap, document.getElementById("eventBuilder"));
	    eventSelector.id = "eventSelector";
	    document.getElementById("eventBuilder").appendChild(eventSelector);
	    self.renderMainConnector("and", document.getElementById("eventBuilder"));
	    self.addNesting(document.getElementById("eventBuilder"), "and");
	    self.createActionBuilder(document.getElementById("actionBuilder"));
	},
	update : function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext) {
	    // IGNORE, we don't have to do anything on update (yet) ...
	    // Will be needed for edit
	}
    };
}

/**
 * Initalizes the model
 */
function init_eventConfig() {
    model = new eventConfig();

    model.mainTemplate = function() {
	return "configuration/events";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}