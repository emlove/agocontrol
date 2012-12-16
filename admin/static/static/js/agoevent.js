
function add_nesting(container, type) {
	var dl = document.createElement("dl");
	var dd = document.createElement("dd");
	dl.setAttribute("class", "operator");

	var subList = document.createElement("dl");
	subList.setAttribute("class", "subList");
	
	dl.appendChild(dd);
	dd.appendChild(document.createTextNode("Operator: "));
	//dd.appendChild(document.createTextNode("Operator");

	var radio = document.createElement("input");
	radio.name = "op_" + (current_id);
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
	radio.name = "op_" + (current_id);
	radio.id = radio.name + "_or";
	radio.type = "radio";
	radio.value = "or";
	radio.checked = (type == "or");
	var label = document.createElement("label");
	label.appendChild(document.createTextNode("or"));
	label.setAttribute("for", radio.name);
	dd.appendChild(radio);
	dd.appendChild(label);

    current_id++;

	var adSbutton = document.createElement("button");
	adSbutton.appendChild(document.createTextNode("Add criteria"));
	adSbutton._list = subList;
	adSbutton.onclick = function() {
		add_segment(this._list);
	};

	dd.appendChild(adSbutton);

	var adNbutton = document.createElement("button");
	adNbutton.appendChild(document.createTextNode("Add nesting"));
	adNbutton._list = dl;
	adNbutton.onclick = function() {
		add_nesting(this._list.lastChild, "and");
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
		//newParent.appendChild(dl);
		if (parentElem.nextSibling) {
			newParent.insertBefore(dl, parentElem.nextSibling);
		}
		else {
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
		}
		else {
			
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

	return [dl, subList];
}

function add_segment(container, eventObj) {
	var dd = document.createElement("dd");

	var span = document.createElement("span");
	span.className = "eventParams";
	var selector = null;

	dd.appendChild(span);

	if (eventObj) {
		render_event(eventObj.path, eventMap[eventObj.path], span, eventObj);
	}
	else {
		var selector = document.getElementById("eventSelector");
		render_event(selector.options[selector.selectedIndex].value, eventMap[selector.options[selector.selectedIndex].value], span);
	}
	
	var button = document.createElement("button");
	button.appendChild(document.createTextNode("delete"));
	button._listItem= dd;
	button.onclick = function() {
		this._listItem.parentNode.removeChild(this._listItem);
	};
	dd.appendChild(button);
	container.appendChild(dd);	
}

function op_to_json(tmp) {
	var op = {};
	op.sub = [];
	var radios = tmp.firstChild.getElementsByTagName("input");
	for (var j = 0; j < radios.length; j++) {
		if (radios[j].checked) {
			op.type = radios[j].value;
		}
	}

	if (tmp.getElementsByClassName("subList").length > 0) {
		var subList = tmp.getElementsByClassName("subList")[0];
		for (var j = 0; j < subList.childNodes.length; j++) {	
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
		for (var j = 0; j < subOps.length; j++) {
			if (subOps[j].className == "operator") {
				op.sub.push(op_to_json(subOps[j]));
			}
		}
	}

	return op;
}

function create_json(uuid) {
	var ops = document.getElementsByClassName("operator");
	var res = [];
	for (var i = 0; i < ops.length; i++) {
		if (ops[i].parentNode != document.getElementById("eventBuilder")) {
			continue;
		}
		res.push(op_to_json(ops[i]));
	}
	var eventSelector = document.getElementById("eventSelector");
	res = {"conn" : document.getElementById("conn_and").checked ? "and" : "or", "elements" : res, "path" : eventSelector.options[eventSelector.selectedIndex].value};
	
	var action = {};
	action.command = document.getElementById("commandSelect").options[document.getElementById("commandSelect").selectedIndex].value;
	action.uuid = devices[document.getElementById("deviceSelect").options[document.getElementById("deviceSelect").selectedIndex].value].id;

    var event_name = document.getElementById("event_name").value;

	var http = new XMLHttpRequest();
	var request = "data=" + encodeURIComponent(JSON.stringify(res)) + "&action="  + encodeURIComponent(JSON.stringify(action)) +
	              "&event_name=" + encodeURIComponent(JSON.stringify(event_name));
	if (uuid) {
    	http.open("POST", "/event/do_edit", true);
    	request += "&uuid="  + uuid;
    }
    else {
        http.open("POST", "/event/save", true);
    }
	http.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
	http.onreadystatechange =  function() {
		if (http.readyState == 4) {
		    if (http.responseText == "OK") {
		        document.location.href = "/event";
		    }
		    else {
		        alert("Error while sending request!");
		    }
		}
	};
	http.send(request);
}

function create_op(sub, container, type) {
    var res =  add_nesting(container, type);
	var dl = res[0];
	var subList = res[1];
	for (var i = 0; i < sub.length; i++) {
		if (sub[i].type) {
			create_op(sub[i].sub, dl.lastChild, sub[i].type);
		}
		else {
			add_segment(subList, sub[i]); 
		}
	}
}

function json_to_list(str, container) {
    var input = JSON.parse(str);

	document.getElementById("eventBuilder").innerHTML = "";
	var eventSelector = get_event_selector(eventMap, document.getElementById("eventBuilder"));
	eventSelector.id = "eventSelector";
	document.getElementById("eventBuilder").appendChild(eventSelector);
    render_main_connector(input.conn, document.getElementById("eventBuilder"));
    
	var inputList = input.elements;
	for (var i = 0; i < inputList.length; i++) {
		var op = inputList[i];
		var tmp = create_op(op.sub, document.getElementById("eventBuilder"), op.type);
	}

	var eventSelector = document.getElementById("eventSelector");
	for (var i = 0; i < eventSelector.options.length; i++) {
		if (eventSelector.options[i].value == input.path) {
			eventSelector.options[i].selected = true;
			break;
		}
	}
	
}

function get_event_selector(events, container, defaultPath) {
	var eventList = document.createElement("select");
	eventList.onchange = function() {
		var path = eventList.options[eventList.selectedIndex].value;
		var eventParams = document.getElementsByClassName("eventParams");
		for (var i = 0; i < eventParams.length; i++) {
			render_event(path, events[path], eventParams[i]);
		}
	}
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
}

function render_main_connector(type, container) {
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
} 

function render_event(path, event, container, defaultValues) {
	container.innerHTML = "";

	var params = document.createElement("select");
	params.name = path + ".param";
	if (event.parameters !== undefined) {
		for (var i = 0; i < event.parameters.length; i++) {
			var opt = new Option(event.parameters[i],  event.parameters[i]);
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
		    for (var i = 0; comp.options.length; i++) {
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
}



function create_action_builder(container, defaults) {
    var deviceSelect = document.createElement("select");
    deviceSelect.id = "deviceSelect";
    var commandSelect = document.createElement("select");
    commandSelect.id = "commandSelect";
    var commandParams = document.createElement("fieldset");
    var j = 0;
    for (var i = 0; i < devices.length; i++) {
        var dev = devices[i];
        if (deviceTypes[dev.devicetype] === undefined || deviceTypes[dev.devicetype].commands.length == 0) {
            continue;
        }
        deviceSelect.options[j] = new Option(dev["name"] == "" ? dev["id"] : dev["name"], i);
        if (defaults && defaults.uuid == dev["id"]) {
            deviceSelect.options[j].selected = true;
        }
        j++;
    }
   
    container.appendChild(deviceSelect);
    container.appendChild(commandSelect);
    container.appendChild(commandParams);
    

    deviceSelect.onchange = function() {
        if (deviceSelect.options[deviceSelect.selectedIndex] == undefined) {
            return;
        }
        var idx = deviceSelect.options[deviceSelect.selectedIndex].value;
        create_command_selector(commandSelect, commandParams, devices[idx].devicetype);
    };
    if (!defaults) {
        deviceSelect.onchange();
    }
    else {
        var idx = deviceSelect.options[deviceSelect.selectedIndex].value;
        create_command_selector(commandSelect, commandParams, devices[idx].devicetype, defaults);       
    }
}   

function create_command_selector(commandSelect, commandParams, type, defaults) {
    commandSelect.options.length = 0;
    for (var i = 0; i < deviceTypes[type].commands.length; i++) {
        commandSelect.options[i] = new Option(commands[deviceTypes[type].commands[i]].name, deviceTypes[type].commands[i]);
        if (defaults && defaults.command == deviceTypes[type].commands[i]) {
            commandSelect.options[i].selected = true;
        }
    }
    commandSelect.onchange = function() {
        var cmd = commands[commandSelect.options[commandSelect.selectedIndex].value];
        commandParams.innerHTML = "";
        if (cmd.parameters !== undefined) {
            commandParams.style.display = "";
            var legend = document.createElement("legend");
            legend.style.fontWeight = 700;
            legend.appendChild(document.createTextNode("Parameters"));
            commandParams.appendChild(legend);
            for (var param in cmd.parameters) {
                var label = document.createElement("label");
                label.appendChild(document.createTextNode(cmd.parameters[param].name + ": " ));
                label.for = cmd.parameters[param].name;
                commandParams.appendChild(label);

                var input = document.createElement("input");
                input.name = cmd.parameters[param].name;
                input.id = cmd.parameters[param].name;
                input.className = "cmdParam";
                commandParams.appendChild(input);
                
                var br = document.createElement("br");
                commandParams.appendChild(br);
            }
        }
        else {
            commandParams.style.display = "none";
        }
    };

    commandSelect.onchange();
}
