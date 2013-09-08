/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function floorPlanConfig() {
    this.hasNavigation = ko.observable(true);
    this.floorplans = ko.observableArray([]);

    var self = this;

    this.makeEditable = function() {
	var eTable = $("#floorPlanTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#floorPlanTable").dataTable();
	eTable.$('td.edit_fp').editable(function(value, settings) {
	    var content = {};
	    content.floorplan = $(this).data('uuid');
	    content.uuid = agoController;
	    content.command = "setfloorplanname";
	    content.name = value;
	    sendCommand(content);
	    return value;
	}, {
	    data : function(value, settings) {
		return value;
	    },
	    onblur : "cancel"
	});
    };

    this.deletePlan = function(item, event) {
	$('#floorPlanTable').block({
	    message : '<div>Please wait ...</div>',
	    css : {
		border : '3px solid #a00'
	    }
	});
	var content = {};
	content.floorplan = item.uuid;
	content.uuid = agoController;
	content.command = 'deletefloorplan';
	sendCommand(content, function(res) {
	    console.log(res);
	    if (res.result && res.result.returncode == 0) {
		self.floorplans.remove(function(e) {
		    return e.uuid == item.uuid;
		});
		$("#floorPlanTable").dataTable().fnDeleteRow(event.target.parentNode.parentNode);
		$("#floorPlanTable").dataTable().fnDraw();
	    } else {
		alert("Error while deleting floorplan!");
	    }
	    $('#floorPlanTable').unblock();
	});
    };

}

/**
 * Initalizes the model
 */
function init_floorplanConfig() {
    model = new floorPlanConfig();

    model.mainTemplate = function() {
	return "configuration/floorplan";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
