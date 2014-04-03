/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function variablesConfig() {
    this.hasNavigation = ko.observable(true);
    this.variables = ko.observableArray([]);

    var self = this;

    this.makeEditable = function(row) {
	window.setTimeout(function() {
	    $(row).find('td.edit_var').editable(function(value, settings) {
		var content = {};
		content.variable = $(this).data('variable');
		content.uuid = agoController;
		content.command = "setvariable";
		content.value = value;
		sendCommand(content);
		return value;
	    }, {
		data : function(value, settings) {
		    return value;
		},
		onblur : "cancel"
	    });
	}, 1);
    };

    this.createVariable = function(data, event) {
	$('#configTable').block({
	    message : '<div>Please wait ...</div>',
	    css : {
		border : '3px solid #a00'
	    }
	});
	var content = {};
	content.variable = $("#varName").val();
	content.value = "True";
	content.command = 'setvariable';
	content.uuid = agoController;
	sendCommand(content, function(res) {
	    console.log(res);
	    if (res.result && res.result.returncode == 0) {
		self.variables.push({
		    variable : content.variable,
		    value : content.value
		});
	    } else {
		alert("Error while creating variable!");
	    }
	    $('#configTable').unblock();
	});
    };

    this.deleteVariable = function(item, event) {
	var button_yes = $("#confirmDeleteButtons").data("yes");
	var button_no = $("#confirmDeleteButtons").data("no");
	var buttons = {};
	buttons[button_no] = function() {
	    $("#confirmDelete").dialog("close");
	};
	buttons[button_yes] = function() {
	    self.doDeleteVariable(item, event);
	    $("#confirmDelete").dialog("close");
	};
	$("#confirmDelete").dialog({
	    modal : true,
	    height : 180,
	    width : 500,
	    buttons : buttons
	});
    };

    this.doDeleteVariable = function(item, event) {
	$('#configTable').block({
	    message : '<div>Please wait ...</div>',
	    css : {
		border : '3px solid #a00'
	    }
	});
	var content = {};
	content.variable = item.variable;
	content.uuid = agoController;
	content.command = 'delvariable';
	sendCommand(content, function(res) {
	    if (res.result && res.result.returncode == 0) {
		self.variables.remove(function(e) {
		    return e.variable == item.variable;
		});
	    } else {
		alert("Error while deleting variable!");
	    }
	    $('#configTable').unblock();
	});
    };

}

/**
 * Initalizes the model
 */
function init_variablesConfig() {
    model = new variablesConfig();

    model.mainTemplate = function() {
	return "configuration/variables";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
