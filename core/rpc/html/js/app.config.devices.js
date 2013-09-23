/**
 * Model class
 * 
 * @returns {deviceConfig}
 */
function deviceConfig() {
    this.devices = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);

    this.makeEditable = function() {
	var eTable = $("#configTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#configTable").dataTable({ "oLanguage": { "sUrl": getDataTableLangUrl() } });
	eTable.$('td.edit_device').editable(function(value, settings) {
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

	eTable.$('td.select_device_room').editable(function(value, settings) {
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
}

/**
 * Initalizes the model
 */
function init_deviceConfig() {
    model = new deviceConfig();

    model.mainTemplate = function() {
	return "configuration/devices";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}