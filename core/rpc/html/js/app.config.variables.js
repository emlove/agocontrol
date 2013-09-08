/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function variablesConfig() {
    this.hasNavigation = ko.observable(true);
    this.variables = ko.observableArray([]);

    var self = this;

    this.makeEditable = function() {
	var eTable = $("#configTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#configTable").dataTable();
	eTable.$('td.edit_var').editable(function(value, settings) {
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
		$("#configTable").dataTable().fnDeleteRow(event.target.parentNode.parentNode);
		$("#configTable").dataTable().fnDraw();
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
