/**
 * Model class
 * 
 * @returns
 */
function eventConfig() {
    this.hasNavigation = ko.observable(true);
    this.devices = ko.observableArray([]);
    this.events = ko.observableArray([]);

    var self = this;
    this.openEvent = null;
    this.current_id = 0;
    this.map = {};
    this.eventMap = {};
    this.deviceList = {};
    this.builderStepByStepInitialized = false;

    this.devices.subscribe(function() {
	if (self.events().length > 0) {
	    return;
	}
	var tmp = [];
	for ( var i = 0; i < self.devices().length; i++) {
	    var dev = self.devices()[i];
	    if (dev.devicetype == "event") {
		tmp.push(dev);
	    }
	}
	/* No events add a dummy to trigger afterRender */
	if (tmp.length == 0) {
	    tmp.push({
		name : "dummy",
		uuid : "0"
	    });
	}
	
	self.events(tmp);
	
	self.eventMap = schema.events;
	self.deviceList = deviceMap;
    });

    /**
     * Initalizes the empty event creation builder
     */
    this.initBuilder = function() {
	self.eventMap = schema.events;
	self.deviceList = deviceMap;

    //init tabs
    $("#tabs").tabs();

    //init blockly
    Blockly.inject(document.getElementById('blocklyDiv'), {path: './blockly/', toolbox: document.getElementById('toolbox')});
    if( Agocontrol.init!==undefined )
        Agocontrol.init(schema, deviceMap);
    else
        console.log('Agocontrol is undefined!. Blockly not configured');

	// Clean
	document.getElementsByClassName("eventBuilder")[0].innerHTML = "";
	document.getElementById("actionBuilder").innerHTML = "";

	// Build new
	var eventSelector = self.getEventSelector(self.eventMap, document.getElementsByClassName("eventBuilder")[0]);
	eventSelector.id = "eventSelector";
	document.getElementsByClassName("eventBuilder")[0].appendChild(eventSelector);
	self.renderMainConnector("and", document.getElementsByClassName("eventBuilder")[0]);
	self.addNesting(document.getElementsByClassName("eventBuilder")[0], "and");
	self.createActionBuilder(document.getElementById("actionBuilder"));
    };

    //init step by step event builder
    this.initStepByStepBuilder = function() 
    {
        self.deviceList = deviceMap;
        self.fillAvailableDeviceTypes();
    }

    /**
     * Callback for editable table
     */
    this.makeEditable = function() {
	var eTable = $("#configTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#configTable").dataTable();
	eTable.$('td.edit_event').editable(function(value, settings) {
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

	// Initial build
	if (!document.getElementsByClassName("eventBuilder")[0]._set) {
	    self.initBuilder();
	    document.getElementsByClassName("eventBuilder")[0]._set = true;
    }

    
    if( !self.builderStepByStepInitialized )
    {
        self.initStepByStepBuilder();
        self.builderStepByStepInitialized = true;
    }

	self.events.remove(function(ev) {
	    return ev.uuid == '0';
	});

    };

    /* Used for parsing event into JSON structure */
    this.getCriteriaIdx = function(str) {
	var regex = /.+([0-9]).+/g;
	var matches = regex.exec(str);
	if (!matches) {
	    return false;
	}
	return matches[1];
    };

    /* Used for parsing event into JSON structure */
    this.parseGroup = function(str, criteria) {
	var sub = [];
	var type = "and";
	str = str.replace(/(^\()|(\)$)/g, "");
	var data = str.split(/(and|or)/g);

	for ( var i = 0; i < data.length; i++) {
	    var tmp = data[i];
	    if (tmp == "and" || tmp == "or") {
		type = tmp;
		continue;
	    }
	    if ($.trim(tmp)[0] == "(") {
		var next = "";
		for ( var j = i; j < data.length; j++) {
		    next += data[j];
		}
		sub.push(self.parseGroup($.trim(next).replace(/(^\()|(\)$)/g, ""), criteria));
		break;
	    }
	    var idx = self.getCriteriaIdx(tmp);
	    if (idx !== false) {
		sub.push(criteria[idx]);
	    }
	}

	return {
	    "sub" : sub,
	    "type" : type
	};
    };

    /* Used for parsing event into JSON structure */
    this.mapToJSON = function(input) {
	var criteria = {};
	for ( var idx in input.criteria) {
	    criteria[idx] = {};
	    criteria[idx].path = input.event;
	    criteria[idx].comp = input.criteria[idx].comp;
	    criteria[idx].param = input.criteria[idx].lval;
	    criteria[idx].value = input.criteria[idx].rval;
	}

	var res = {};
	res.conn = "and";
	if (input.nesting == "True") {
	    res.elements = [];
	} else {
	    res.elements = [ self.parseGroup(input.nesting, criteria) ];
	}
	res.path = input.event;

	return res;
    };

    /**
     * Opens edit event dialog
     */
    this.editEvent = function(item) {
	var content = {};
	content.command = "getevent";
	content.event = item.uuid;
	content.uuid = eventController;
	sendCommand(content, function(res) {
	    // Swap active selector
	    document.getElementById("eventBuilder").className = "";
	    document.getElementById("eventBuilderEdit").className = "eventBuilder";

	    // Disable main one to avoid id conflicts
	    document.getElementById("eventBuilder").innerHTML = "";
	    document.getElementById("actionBuilder").innerHTML = "";

	    // Create prepopulated builders
	    self.buildListFromJSON(self.mapToJSON(res.result.eventmap), document.getElementById("eventBuilderEdit"));
	    self.createActionBuilder(document.getElementById("actionBuilderEdit"), res.result.eventmap.action);

	    // Save the id (needed for the save command)
	    self.openEvent = item.uuid;

	    // Open the dialog
	    if (document.getElementById("editEventDialogTitle")) {
		$("#editEventDialog").dialog({
		    title : document.getElementById("editEventDialogTitle").innerHTML,
		    modal : true,
		    width : 900,
		    height : 600,
		    close : function() {
			// Done, restore stuff
			document.getElementById("eventBuilderEdit").className = "";
			document.getElementById("eventBuilder").className = "eventBuilder";
			self.initBuilder();
			self.openEvent = null;
		    }
		});
	    }
	});
    };

    /**
     * Sends the event edit command
     */
    this.doEditEvent = function() {
	this.createEventMap(self.createJSON());
	var content = {};
	content.uuid = eventController;
	content.command = "setevent";
	content.eventmap = self.map;
	content.event = self.openEvent;
	sendCommand(content, function(res) {
	    if (res.result && res.result.event) {
		$("#editEventDialog").dialog("close");
	    }
	});
    };

    /**
     * Sends the create event commands
     */
    this.createEvent = function() {
	if ($("#eventName").val() == "") {
	    alert("Please supply an event name!");
	    return;
	}

	this.createEventMap(self.createJSON());

	var content = {};
	content.uuid = eventController;
	content.command = "setevent";
	content.eventmap = self.map;

	sendCommand(content, function(res) {
	    if (res.result && res.result.event) {
		var cnt = {};
		cnt.uuid = agoController;
		cnt.device = res.result.event;
		cnt.command = "setdevicename";
		cnt.name = $("#eventName").val();
		sendCommand(cnt, function(nameRes) {
		    if (nameRes.result && nameRes.result.returncode == "0") {
			self.events.push({
			    name : cnt.name,
			    uuid : res.result.event
			});
			self.initBuilder();
		    }
		});
	    } else {
		alert("ERROR");
	    }
	});
    };

    this.deleteEvent = function(item, event) {
	var button_yes = $("#confirmDeleteButtons").data("yes");
	var button_no = $("#confirmDeleteButtons").data("no");
	var buttons = {};
	buttons[button_no] = function() {
	    $("#confirmDelete").dialog("close");
	};
	buttons[button_yes] = function() {
	    self.doDeleteEvent(item, event);
	    $("#confirmDelete").dialog("close");
	};
	$("#confirmDelete").dialog({
	    modal : true,
	    height : 180,
	    width : 500,
	    buttons : buttons
	});
    };

    /**
     * Sends the delete event command
     */
    this.doDeleteEvent = function(item, event) {
	$('#configTable').block({
	    message : '<div>Please wait ...</div>',
	    css : {
		border : '3px solid #a00'
	    }
	});
	var content = {};
	content.event = item.uuid;
	content.uuid = eventController;
	content.command = 'delevent';
	sendCommand(content, function(res) {
	    if (res.result && res.result.result == 0) {
		self.events.remove(function(e) {
		    return e.uuid == item.uuid;
		});
		$("#configTable").dataTable().fnDeleteRow(event.target.parentNode.parentNode);
		$("#configTable").dataTable().fnDraw();
	    } else {
		alert("Error while deleting event!");
	    }
	    $('#configTable').unblock();
	});
    };

    /**
     * Helper for event map creation
     */
    this.parseElement = function(element) {
	// 'empty' events like 'sun did rise'
	if (element.sub === undefined) {
	    return "True";
	}

	var nesting = "";

	for ( var j = 0; j < element.sub.length; j++) {
	    var obj = element.sub[j];
	    if (obj.param !== undefined) {
		self.map.criteria[self.idx] = {};
		self.map.criteria[self.idx].lval = obj.param;
		self.map.criteria[self.idx].comp = obj.comp;
		self.map.criteria[self.idx].rval = obj.value;
		if (nesting == "") {
		    nesting += "(criteria[" + self.idx + "]";
		} else {
		    nesting += " " + element.type + " criteria[" + self.idx + "]";
		}
		self.idx = self.idx + 1;
	    } else {
		nesting += " " + element.type + " (" + self.parseElement(obj) + ")";
	    }
	}

	if (nesting == "") {
	    return "(True)";
	}

	return nesting + ")";

    };

    /**
     * Creates the event map for the resolver
     */
    this.createEventMap = function(data) {
	self.map = {};
	self.map.criteria = {};
	self.map.nesting = "";
	self.map.event = data.path;

	self.idx = 0;

	for ( var i = 0; i < data.elements.length; i++) {
	    self.map.nesting += self.parseElement(data.elements[i]);
	    self.idx = self.idx + 1;
	}

	// Add the toplevel operator
	self.map.nesting = self.map.nesting.replace(/\)\(/g, ") " + data.conn + " (");

	// Remove useless and/or suffixes
	self.map.nesting = $.trim(self.map.nesting);
	self.map.nesting = self.map.nesting.replace(/^(and|or)/g, "");
	self.map.nesting = $.trim(self.map.nesting);

	if (self.map.criteria == {}) {
	    self.map.nesting = "True";
	}

	// Set the action
	self.map.action = {};
	self.map.action.command = document.getElementById("commandSelect").options[document.getElementById("commandSelect").selectedIndex].value;
	self.map.action.uuid = self.deviceList[document.getElementById("deviceListSelect").options[document.getElementById("deviceListSelect").selectedIndex].value].uuid;

	var paramList = document.getElementsByClassName("cmdParam");
    if (paramList)
    {
        for( var i=0; i<paramList.length; i++)
        {
            self.map.action[paramList[i].id] = paramList[i].value;
        }
    }
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
	    if (this._list.parentNode == document.getElementsByClassName("eventBuilder")[0] && document.getElementsByClassName("operator").length == 1) {
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
	    if (this._list.parentNode == document.getElementsByClassName("eventBuilder")[0]) {
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
	    self.renderEvent(eventObj.param.type, eventObj.path, self.eventMap[eventObj.path], span, eventObj);
	} else {
	    var selector = document.getElementById("eventSelector");
	    self.renderEvent("event", selector.options[selector.selectedIndex].value, self.eventMap[selector.options[selector.selectedIndex].value], span);
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
		    var type = selects[0].options[selects[0].selectedIndex].value;
		    if (type == "event") {
			eventObj.comp = selects[2].options[selects[2].selectedIndex].value;

			eventObj.param = {};
			eventObj.param.type = "event";
			eventObj.param.parameter = selects[1].options[selects[1].selectedIndex].value;

			eventObj.value = subList.childNodes[j].getElementsByTagName("input")[0].value;
		    } else if (type == "device") {
			eventObj.comp = selects[3].options[selects[3].selectedIndex].value;

			eventObj.param = {};
			eventObj.param.type = "device";
			eventObj.param.uuid = selects[1].options[selects[1].selectedIndex].value;
			eventObj.param.parameter = selects[2].options[selects[2].selectedIndex].value;

			eventObj.value = subList.childNodes[j].getElementsByTagName("input")[0].value;
		    }
		    if (type == "variable") {
			eventObj.comp = selects[2].options[selects[2].selectedIndex].value;
			eventObj.param = {};
			eventObj.param.type = "variable";
			eventObj.param.name = selects[1].options[selects[1].selectedIndex].value;
			eventObj.value = subList.childNodes[j].getElementsByTagName("input")[0].value;
		    }
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
     * Create a JSON structure out of the whole event
     */
    this.createJSON = function() {
	var ops = document.getElementsByClassName("operator");
	var res = [];
	for ( var i = 0; i < ops.length; i++) {
	    if (ops[i].parentNode != document.getElementsByClassName("eventBuilder")[0]) {
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

	return res;
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
    this.buildListFromJSON = function(input, container) {
	document.getElementsByClassName("eventBuilder")[0].innerHTML = "";
	var eventSelector = self.getEventSelector(self.eventMap, document.getElementsByClassName("eventBuilder")[0]);
	eventSelector.id = "eventSelector";
	document.getElementsByClassName("eventBuilder")[0].appendChild(eventSelector);
	self.renderMainConnector(input.conn, document.getElementsByClassName("eventBuilder")[0]);

	var inputList = input.elements;
	for ( var i = 0; i < inputList.length; i++) {
	    var op = inputList[i];
	    self.createOperation(op.sub, document.getElementsByClassName("eventBuilder")[0], op.type);
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
		self.renderEvent("event", path, events[path], eventParams[i]);
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
    this.renderEvent = function(selectType, path, event, container, defaultValues) {
	container.innerHTML = "";

	var params = null;

	var baseType = document.createElement("select");
	baseType.options[0] = new Option("event", "event");
	baseType.options[1] = new Option("device", "device");
	baseType.options[2] = new Option("variable", "variable");
	container.appendChild(baseType);

	if (selectType == "event") {
	    baseType.selectedIndex = 0;
	} else if (selectType == "device") {
	    baseType.selectedIndex = 1;
	} else if (selectType == "variable") {
	    baseType.selectedIndex = 2;
	}

	baseType.onchange = function() {
	    var type = baseType.options[baseType.selectedIndex].value;
	    self.renderEvent(type, path, event, container, defaultValues);
	};

	if (selectType == "event") {
	    params = document.createElement("select");
	    params.name = path + ".param";
	    if (event.parameters !== undefined) {
		for ( var i = 0; i < event.parameters.length; i++) {
		    var opt = null;
		    if (event.parameters[i] == "uuid") {
			opt = new Option("device", event.parameters[i]);
		    } else {
			opt = new Option(event.parameters[i], event.parameters[i]);
		    }
		    params.options[i] = opt;
		    if (defaultValues && event.parameters[i] == defaultValues.param.parameter) {
			params.options[i].selected = true;
		    }
		}
	    }

	    container.appendChild(params);
	} else if (selectType == "device") {
	    var deviceSelect = document.createElement("select");
	    deviceSelect.name = path + ".device";
	    self.deviceList.sort(function(a, b) {
		return a.room.localeCompare(b.room);
	    });
	    for ( var i = 0; i < self.deviceList.length; i++) {
		if (self.deviceList[i].name) {
		    var dspName = "";
		    if (self.deviceList[i].room) {
			dspName = self.deviceList[i].room + " - " + self.deviceList[i].name;
		    } else {
			dspName = self.deviceList[i].name;
		    }
		    deviceSelect.options[deviceSelect.options.length] = new Option(dspName, self.deviceList[i].uuid);
		    if (defaultValues && self.deviceList[i].uuid == defaultValues.param.uuid) {
			deviceSelect.options[deviceSelect.options.length - 1].selected = true;
		    }
		}
	    }

	    params = document.createElement("select");
	    params.name = path + ".param";

	    var _buildParamList = function(dev) {
		params.options.length = 0;
		params.options[0] = new Option("state", "state");
		if (dev.values) {
		    var i = 0;
		    for ( var k in dev.values()) {
			params.options[i + 1] = new Option(k, k);
			if (defaultValues && k == defaultValues.param.parameter) {
			    params.options[i + 1].selected = true;
			}
			i++;
		    }
		}
	    };

	    _buildParamList(self.deviceList[deviceSelect.options.selectedIndex]);

	    deviceSelect.onchange = function() {
		var selectedUuid = deviceSelect.options[deviceSelect.selectedIndex].value;
		var dev = {};
		for ( var i = 0; i < self.deviceList.length; i++) {
		    if (self.deviceList[i].uuid == selectedUuid) {
			dev = self.deviceList[i];
			break;
		    }
		}
		_buildParamList(dev);
	    };

	    container.appendChild(deviceSelect);
	    container.appendChild(params);
	} else if (selectType == "variable") {
	    params = document.createElement("select");
	    params.name = path + ".param";
	    var i = 0;
	    for ( var k in variables) {
		params.options[i] = new Option(k, k);
		if (defaultValues && k == defaultValues.param.name) {
		    params.options[i].selected = true;
		}
		i++;
	    }
	    container.appendChild(params);
	}

	var comp = document.createElement("select");
	comp.name = path + ".comp";
	comp.options[0] = new Option("=", "eq");
	comp.options[1] = new Option("!=", "new");
	comp.options[2] = new Option(">", "gt");
	comp.options[3] = new Option("<", "lt");
	comp.options[4] = new Option(">=", "gte");
	comp.options[5] = new Option("<=", "lte");

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

	/* Show variable value placeholder */
	if (selectType == "variable") {
	    inputField.setAttribute("placeholder", variables[params.options[0].value]);
	    params.onchange = function() {
		inputField.setAttribute("placeholder", variables[params.options[params.selectedIndex].value]);
	    };
	}

	container.appendChild(comp);
	container.appendChild(inputField);

	/* Add a device selector when someone selects the uuid field of event */
	if (selectType == "event") {
	    var deviceSelect = document.createElement("select");
	    deviceSelect.name = path + ".device";
	    self.deviceList.sort(function(a, b) {
		return a.room.localeCompare(b.room);
	    });
	    for ( var i = 0; i < self.deviceList.length; i++) {
		if (self.deviceList[i].name) {
		    var dspName = "";
		    if (self.deviceList[i].room) {
			dspName = self.deviceList[i].room + " - " + self.deviceList[i].name;
		    } else {
			dspName = self.deviceList[i].name;
		    }
		    deviceSelect.options[deviceSelect.options.length] = new Option(dspName, self.deviceList[i].uuid);
		    if (defaultValues && defaultValues.param.parameter == "uuid" && self.deviceList[i].uuid == defaultValues.value) {
			deviceSelect.selectedIndex = deviceSelect.options.length - 1;
		    }
		}
	    }
	    deviceSelect.onchange = function() {
		inputField.value = deviceSelect.options[deviceSelect.selectedIndex].value;
	    };
	    deviceSelect.style.display = "none";
	    container.appendChild(deviceSelect);
	    params.onchange = function() {
		if (params.options[params.selectedIndex].value == "uuid") {
		    deviceSelect.style.display = "";
		    inputField.style.display = "none";
		} else {
		    deviceSelect.style.display = "none";
		    inputField.style.display = "";
		    inputField.value = "";
		}
	    };
	    if (defaultValues && defaultValues.param.parameter == "uuid") {
		params.onchange();
	    }
	}

    };

    /**
     * Creates the action builder
     */
    this.createActionBuilder = function(container, defaults) {
	container.innerHTML = "";
	var deviceListSelect = document.createElement("select");
	deviceListSelect.id = "deviceListSelect";
	var commandSelect = document.createElement("select");
	commandSelect.id = "commandSelect";
	var commandParams = document.createElement("fieldset");
	var j = 0;
	self.deviceList.sort(function(a, b) {
	    return a.room.localeCompare(b.room);
	});
	for ( var i = 0; i < self.deviceList.length; i++) {
	    var dev = self.deviceList[i];
	    if (schema.devicetypes[dev.devicetype] === undefined || schema.devicetypes[dev.devicetype].commands.length == 0) {
		continue;
	    }
	    if (self.deviceList[i].name) {
		var dspName = "";
		if (self.deviceList[i].room) {
		    dspName = self.deviceList[i].room + " - " + self.deviceList[i].name;
		} else {
		    dspName = self.deviceList[i].name;
		}
		deviceListSelect.options[j] = new Option(dspName, i);
		if (defaults && defaults.uuid == dev["uuid"]) {
		    deviceListSelect.options[j].selected = true;
		}
		j++;
	    }
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

            if( cmd.parameters[param].type=='option' )
            {
                var select = document.createElement("select");
                select.name = cmd.parameters[param].name;
                select.className = "cmdParam";
                select.id = cmd.parameters[param].name;
                for( var i=0; i<cmd.parameters[param].options.length; i++ )
                    select.options[select.options.length] = new Option(cmd.parameters[param].options[i], cmd.parameters[param].options[i]);
                commandParams.appendChild(select);
            }
            else
            {
               var input = document.createElement("input");
               input.name = cmd.parameters[param].name;
               input.id = cmd.parameters[param].name;
               input.className = "cmdParam";
               if (defaults && defaults[cmd.parameters[param].name])
               {
                   input.value = defaults[cmd.parameters[param].name];
               } 
               commandParams.appendChild(input);
            }

            var br = document.createElement("br");
            commandParams.appendChild(br);
		}
	    } else {
		commandParams.style.display = "none";
	    }
	};

	commandSelect.onchange();
    };


    //STEP BY STEP EVENT BUILDER========================================================
    //---------------------------------------
    //utils
    //---------------------------------------
    var Event = function() {
        //this.deviceType = undefined;
        //this.deviceUuid = undefined;
        //this.deviceName = undefined;
        this.triggers = [];
        this.conditions = [];
        this.actionsThen = [];
        this.actionsElse = [];
    };
    self.currentEvent = new Event();

    var Trigger = function() {
        this.deviceType = undefined;
        this.deviceName = undefined;
        this.deviceUuid = undefined;
        this.event = undefined;
    };

    var Condition = function() {
        this.andOr = undefined;
        this.deviceName = undefined;
        this.deviceUuid = undefined;
        this.propName = undefined;
        this.propType = undefined;
        //options
        this.option = undefined;
        //moptions
        this.options = [];
        //bool
        this.bool = undefined;
        //time
        this.time = undefined;
        //range
        this.rangeMin = undefined;
        this.rangeMax = undefined;
        //threshold
        this.thresholdSign = undefined;
        this.thresholdValue = undefined;
        //timeoffset
        this.timeOffsetSign = undefined;
        this.timeOffsetValue = undefined;
    };

    var CommandParameter = function() {
        this.name = undefined;
        this.desc = undefined;
        this.type = undefined;
        this.options = [];
    };

    var Action = function() {
        this.deviceName = undefined;
        this.deviceUuid = undefined;
        this.action = undefined;
        this.actionDesc = undefined;
        this.parameters = [];
    };

    var ActionParameter = function() {
        this.name = undefined;
        this.type = undefined;
        this.value = undefined;
    };

    var SbSOption = function(key,value) {
        this.optionKey = key;
        this.optionValue = value;
    }

    //---------------------------------------
    //trigger picker
    //---------------------------------------
    self.availableDeviceTypes = ko.observableArray([]);
    self.selectedDeviceType = ko.observable();
    self.availableDevices = ko.observableArray([]);
    self.selectedDevice = ko.observable();
    self.availableDeviceEvents = ko.observableArray([]);
    self.selectedDeviceEvent = ko.observable();
    self.hasSelectedDevice = ko.computed(function() {
        if( self.selectedDevice()!==undefined )
            return true;
        else
            return false;
    });

    //fill available device types
    this.fillAvailableDeviceTypes = function() {
        var found = 0;
        for ( var i = 0; i < self.deviceList.length; i++)
        {
            var dev = self.deviceList[i];

            //check device validity
            //TODO add here useless device types
            if( schema.devicetypes[dev.devicetype]===undefined )
                continue;
            else if( dev.devicetype=='event' || dev.devicetype=='scenario' )
                continue;

            if( self.availableDeviceTypes.indexOf(dev.devicetype)==-1 )
            {
                self.availableDeviceTypes.push(dev.devicetype);
                if( found==0 )
                    self.selectedDeviceType(dev.devicetype);
                found++;
            }
        }
    };

    //fill available devices
    this.fillAvailableDevices = function() {
        var found = 0;
        self.availableDevices([]);

        //fill with new content
        for ( var i=0; i<self.deviceList.length; i++)
        {
            var dev = self.deviceList[i];

            //check device validity
            if( schema.devicetypes[dev.devicetype]===undefined )
            {
                //device has problem, drop it
                continue;
            }

            //add device to list
            if( dev.name!==undefined && dev.name.length>0 && dev.devicetype==self.selectedDeviceType() )
            {
                var option = new SbSOption(dev.uuid, dev.name);
                self.availableDevices.push(option);
                if( found==0 )
                    self.selectedDevice(option);
                found++;
            }
        }
        if( found==0 )
            self.selectedDevice('');
    };
    //fill automatically devices list when device type is modified
    self.selectedDeviceType.subscribe(self.fillAvailableDevices);


    //fill available events for specified device type
    this.fillAvailableDeviceEvents = function() {
        //init
        var found = 0;
        self.availableDeviceEvents([]);
        deviceType = self.selectedDeviceType();

        //fill events list
        if( deviceType!==undefined && schema.devicetypes[deviceType].events!==undefined )
        {
            for( var i=0; i<schema.devicetypes[deviceType].events.length; i++ )
            {
                //fill with new content
                devEvent = schema.devicetypes[deviceType].events[i];
                self.availableDeviceEvents.push(devEvent);
                if( found==0 )
                    self.selectedDeviceEvent(devEvent);
                found++;
            }
        }
        //if( found==0 )
        //    self.availableDeviceEvents.push('<device has no event>');
    }
    self.selectedDevice.subscribe(self.fillAvailableDeviceEvents);

    self.triggerPicker = function(deviceType, deviceUuid, callback) {
        //pre-select device type and device if necessary
        if( deviceType!==undefined && deviceUuid!==undefined )
        {
            self.selectedDeviceType(deviceType);
            self.selectedDevice(deviceUuid);
        }

        //TODO select deviceType and  deviceName automatically
        $("#dialogTriggerPicker").dialog({
            resizable: true,
            modal: true,
            height: 200,
            width: 550,
            buttons: {
                'Ok': function() {
                    if( self.selectedDeviceType()!==undefined && self.selectedDeviceType().length>0 && self.selectedDevice()!==undefined ) {
                        var trig = new Trigger();
                        trig.deviceType = self.selectedDeviceType();
                        trig.deviceName = self.selectedDevice().optionValue;
                        trig.deviceUuid = self.selectedDevice().optionKey;
                        trig.event = self.selectedDeviceEvent();
                        if( callback!==undefined )
                            callback(trig);
                    }
                    $(this).dialog('close');
                },
                'Cancel': function() {
                    $(this).dialog('close');
                }
            }
        });
    };

    //------------------------------------------
    //condition picker
    //------------------------------------------
    self.availableDeviceProperties = ko.observableArray([]);
    self.selectedDeviceProperty = ko.observable();
    self.selectedDevicePropertyType = ko.observable();
    self.dialogConditionPickerDeviceType = ko.observable();
    self.dialogConditionPickerFirstCond = ko.observable(true);

    self.selectedAndOr = ko.observable();
    self.availablePropertyOptions = ko.observableArray([]);
    self.selectedPropertyOption = ko.observable();
    self.selectedPropertyOptions = ko.observableArray([]);
    self.selectedPropertyTime = ko.observable();
    self.availablePropertyBools = ko.observableArray([]);
    self.selectedPropertyBool = ko.observable();
    self.selectedPropertyRangeMin = ko.observable();
    self.selectedPropertyRangeMax = ko.observable();
    self.selectedPropertyRangeText = ko.computed( function() {
        return '['+self.selectedPropertyRangeMin()+'-'+self.selectedPropertyRangeMax()+']';
    });
    self.selectedPropertyThresholdSign = ko.observable();
    self.selectedPropertyThresholdValue = ko.observable();
    self.selectedPropertyTimeOffsetSign = ko.observable();
    self.selectedPropertyTimeOffsetValue = ko.observable();

    //fill available device properties
    this.fillAvailableDeviceProperties = function(deviceType) {
        //init
        var found = 0;
        self.availableDeviceProperties([]);
        self.dialogConditionPickerDeviceType(deviceType);

        //fill available properties
        if( schema.devicetypes[deviceType].properties!==undefined )
        {
            //for( var prop in schema.devicetypes[deviceType].properties )
            for( var i=0; i<schema.devicetypes[deviceType].properties.length; i++)
            {
                var prop = schema.devicetypes[deviceType].properties[i];
                self.availableDeviceProperties.push(prop);
                if( found==0 )
                    self.selectedDeviceProperty(prop);
                found++;
            }
        }
        if( found==0 )
        {
            //self.availableDeviceProperties.push('<device has no property>');
            self.selectedDevicePropertyType('');
        }
    }
    //fill automatically devices properties when device type is modified
    self.selectedDeviceType.subscribe(self.fillAvailableDeviceProperties);

    //build device property
    this.buildDeviceProperty = function() {
        //init
        var deviceType = self.dialogConditionPickerDeviceType();
        var deviceProperty = self.selectedDeviceProperty();
        self.availablePropertyOptions([]);

        //hide property content if something not available
        if( deviceType===undefined || deviceType.length==0 || deviceProperty===undefined || deviceProperty.length==0 )
            self.selectedDevicePropertyType('');

        if( deviceType!==undefined && deviceProperty!==undefined && deviceType.length>0 && deviceProperty.length>0 )
        {
            //type = schema.devicetypes[deviceType].properties[deviceProperty].type;
            type = schema.values[deviceProperty].type;
            self.selectedDevicePropertyType(type);
            if( type===undefined ) 
            {
                //should not happened
            }
            else if( type=='option' )
            {
                var first = true;
                //for( var value in schema.devicetypes[deviceType].properties[deviceProperty].values )
                for( var i=0; i<schema.values[deviceProperty].options.length; i++)
                {
                    var value = schema.values[deviceProperty].options[i];
                    //var option = new SbSOption(value, schema.devicetypes[deviceType].properties[deviceProperty].values[value]);
                    var option = new SbSOption(value, value);
                    self.availablePropertyOptions.push(option);
                    if( first )
                    {
                        self.selectedPropertyOption(option);
                        first = false;
                    }
                }
            }
            else if( type=='moptions' )
            {
                for( var value in schema.devicetypes[deviceType].properties[deviceProperty].values )
                {
                    var option = new SbSOption(value, schema.devicetypes[deviceType].properties[deviceProperty].values[value]);
                    self.availablePropertyOptions.push(option);
                }
            }
            else if( type=='bool' )
            {
                self.availablePropertyBools([]);
                var option = new SbSOption("1", schema.devicetypes[deviceType].properties[deviceProperty].true);
                self.availablePropertyBools.push(option);
                self.selectedPropertyBool(option);
                option = new SbSOption("0", schema.devicetypes[deviceType].properties[deviceProperty].false);
                self.availablePropertyBools.push(option);
            }
            else if( type=='range' )
            {
                var min = schema.devicetypes[deviceType].properties[deviceProperty].min;
                var max = schema.devicetypes[deviceType].properties[deviceProperty].max;
                self.selectedPropertyRangeMin(min);
                self.selectedPropertyRangeMax(max);
                $("#eventRangePicker").slider({
                    range: true,
                    min: min,
                    max: max,
                    values: [min, max],
                    change: function(event, ui) { 
                        self.selectedPropertyRangeMin(ui.values[0]);
                        self.selectedPropertyRangeMax(ui.values[1]);
                    }
                });
            }
            else if( type=='time' )
            {
                var date = new Date();
                var sNow = date.getHours()+':'+date.getMinutes();
                $('#eventTimePicker').timepicker({
                    defaultValue: sNow
                });
            }
            else if( type=='threshold' )
            {
                self.selectedPropertyThresholdSign('gt');
                self.selectedPropertyThresholdValue(0);
            }
            else if( type=='timeoffset' )
            {
                $('#eventTimeOffsetPicker').timepicker({
                    defaultValue: '00:00'
                });
            }
            else
            {
                //unmanaged type
                console.log('unmanaged type "'+type+'"');
            }
        }
    };
    self.selectedDeviceProperty.subscribe(self.buildDeviceProperty);

    //open condition picker
    self.conditionPicker = function(firstCondition, deviceType, callback) {
        //TODO check parameters
        //hide and/or select if necessary
        self.dialogConditionPickerFirstCond(firstCondition);
    
        //open dialog
        $("#dialogConditionPicker").dialog({
            resizable: true,
            modal: true,
            height: 250,
            width: 700,
            buttons: {
                'Ok': function() {
                    //fill condition
                    if( self.selectedDevice()!==undefined && self.selectedDeviceProperty()!==undefined && self.selectedDeviceProperty().length>0 )
                    {
                        var cond = new Condition();
                        if( firstCondition )
                            cond.andOr = '';
                        else
                            cond.andOr = self.selectedAndOr();
                        cond.deviceUuid = self.selectedDevice().optionKey;
                        cond.deviceName = self.selectedDevice().optionValue;
                        cond.propName = self.selectedDeviceProperty();
                        cond.propType = self.selectedDevicePropertyType();
                        if( cond.propType===undefined )
                        {
                            //should not happen, close dialog
                            $(this).dialog('close');
                        }
                        else if( cond.propType=='options' )
                        {
                            cond.options = self.selectedPropertyOption();
                        }
                        else if( cond.propType=='moptions' )
                        {
                            cond.moptions = self.selectedPropertyOptions();
                            //console.log(cond.moptions);
                        }
                        else if( cond.propType=='bool' )
                        {
                            cond.bool = self.selectedPropertyBool();
                        }
                        else if( cond.propType=='range' )
                        {
                            cond.rangeMin = self.selectedPropertyRangeMin();
                            cond.rangeMax = self.selectedPropertyRangeMax();
                        }
                        else if( cond.propType=='time' )
                        {
                            cond.time = self.selectedPropertyTime();
                        }
                        else if( cond.propType=='threshold' )
                        {
                            cond.thresholdSign = self.selectedPropertyThresholdSign();
                            cond.thresholdValue = self.selectedPropertyThresholdValue();
                        }
                        else if( cond.propType=='timeoffset' )
                        {
                            cond.timeOffsetSign = self.selectedPropertyTimeOffsetSign();
                            cond.timeOffsetValue = self.selectedPropertyTimeOffsetValue();
                        }
                        else
                        {
                            //TODO add here new property type
                            console.log('Unmanaged property type');
                            $(this).dialog('close');
                        }
                        if( callback!==undefined )
                            callback(cond);
                    }
                    $(this).dialog('close');
                },
                'Cancel': function() {
                    $(this).dialog('close');
                }
            }
        });
    };

    //------------------------------------
    //action picker
    //------------------------------------
    self.availableDeviceCommands = ko.observableArray([]);
    self.selectedDeviceCommand = ko.observable();
    self.selectedCommandParameters = ko.observableArray([]);

    //fill available device commands
    this.fillAvailableDeviceCommands = function(deviceType) {
        //init
        var found = 0;
        self.availableDeviceCommands([]);

        if( self.selectedDevice()!==undefined )
        {
            //fill available properties
            if( schema.devicetypes[deviceType].commands!==undefined )
            {
                for( var i=0; i<schema.devicetypes[deviceType].commands.length; i++ )
                {
                    var cmd = schema.devicetypes[deviceType].commands[i];
                    if( schema.commands[cmd]!==undefined )
                    {
                        var opt = new SbSOption(cmd, schema.commands[cmd].name);
                        self.availableDeviceCommands.push(opt);
                        if( found==0 )
                            self.selectedDeviceCommand(cmd);
                        found++;
                    }
                }
            }
        }
    }
    //fill automatically devices commands when device type is modified
    self.selectedDeviceType.subscribe(self.fillAvailableDeviceCommands);

    //build command and its parameters
    this.buildCommand = function() {
        self.selectedCommandParameters([]);
        if( self.selectedDeviceCommand()!==undefined )
        {
            var cmd = self.selectedDeviceCommand().optionKey;
            if( schema.commands[cmd]!==undefined && schema.commands[cmd].parameters!==undefined )
            {
                for( var param in schema.commands[cmd].parameters )
                {
                    var par = new CommandParameter();
                    par.name = param;
                    par.desc = schema.commands[cmd].parameters[param].name;
                    par.type = schema.commands[cmd].parameters[param].type;
                    if( schema.commands[cmd].parameters[param].options!==undefined )
                    {
                        for( var i=0; i<schema.commands[cmd].parameters[param].options.length; i++ )
                            par.options.push( schema.commands[cmd].parameters[param].options[i] );
                    }
                    self.selectedCommandParameters.push(par);
                }
            }
        }
    };
    self.selectedDeviceCommand.subscribe(self.buildCommand);

    //open action picker
    self.actionPicker = function(callback) {
        //TODO check parameters
    
        //open dialog
        $("#dialogActionPicker").dialog({
            resizable: true,
            modal: true,
            height: 350,
            width: 700,
            buttons: {
                'Ok': function() {
                    //build action
                    var act = new Action();
                    act.deviceName = self.selectedDevice().optionValue;
                    act.deviceUuid = self.selectedDevice().optionKey;
                    act.action = self.selectedDeviceCommand().optionKey;
                    act.actionDesc = self.selectedDeviceCommand().optionValue;
                    for(var i=0; i<self.selectedCommandParameters().length; i++)
                    {
                        var par = new ActionParameter();
                        par.name = self.selectedCommandParameters()[i].name;
                        par.type = self.selectedCommandParameters()[i].type;
                        par.value = $("#"+par.name).val();
                        act.parameters.push(par);
                    }
                    if( callback!==undefined )
                        callback(act);
                    $(this).dialog('close');
                },
                'Cancel': function() {
                    $(this).dialog('close');
                }
            }
        });
    };

    //----------------------------
    //If
    //----------------------------
    self.ifTriggersText = ko.observableArray([]);
    self.hasTriggers = ko.computed( function() {
        if( self.ifTriggersText() && self.ifTriggersText().length>0 )
            return true;
        else
            return false;
    });
    this.setIfTrigger = function(trig) {
        //save selected infos
        self.currentEvent.triggers.push(trig);
        //update ui
        self.ifTriggersText.push(trig);
    };
    this.openIfTriggerPicker = function() {
        self.triggerPicker(self.currentEvent.deviceType, self.currentEvent.deviceUuid, self.setIfTrigger);
    };

    //----------------------------
    //And
    //----------------------------
    self.andConditionsText = ko.observableArray([]);
    self.setAndCondition = function(cond) {
        //save condition in current event
        self.currentEvent.conditions.push(cond);
        //update ui
        self.andConditionsText.push(cond);
    };
    self.openAndConditionPicker = function() {
        self.conditionPicker(self.currentEvent.conditions.length==0 ? true : false, self.currentEvent.deviceType, self.setAndCondition);
    };

    //---------------------------
    //Then
    //---------------------------
    self.thenActionsText = ko.observableArray([]);
    self.setThenAction = function(act) {
        //save action in current event
        self.currentEvent.actionsThen.push(act);
        //update ui
        self.thenActionsText.push(act);
    };
    self.openThenActionPicker = function() {
        self.actionPicker(self.setThenAction);
    }

    //---------------------------
    //Else
    //---------------------------
    self.elseActionsText = ko.observableArray([]);
    self.setElseAction = function(act) {
        //save action in current event
        self.currentEvent.actionsElse.push(act);
        //update ui
        self.elseActionsText.push(act);
    };
    self.openElseActionPicker = function() {
        self.actionPicker(self.setElseAction);
    }

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
