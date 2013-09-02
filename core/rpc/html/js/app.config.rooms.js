/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function roomConfig() {
    this.hasNavigation = ko.observable(true);
    this.rooms = ko.observableArray([]);

    var self = this;

    this.makeEditable = function() {
	var eTable = $("#configRoomsTable").dataTable();
	eTable.fnDestroy();
	eTable = $("#configRoomsTable").dataTable();
	eTable.$('td.edit_room').editable(function(value, settings) {
	    var content = {};
	    content.uuid = $(this).data('uuid');
	    content.command = "setroomname";
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

    this.createRoom = function(data, event) {
	$('#configRoomsTable').block({ 
            message: '<div>Please wait ...</div>', 
            css: { border: '3px solid #a00' } 
        }); 
	var content = {};
	content.name = $("#roomName").val();
	content.command = 'setroomname';
	sendCommand(content, function(res) {
	    if (res.result && res.result.returncode == 0) {
		self.rooms.push({
		    uuid : res.result.uuid,
		    name : content.name,
		    location : ""
		});
	    } else {
		alert("Error while creating room!");
	    }
	    $('#configRoomsTable').unblock();
	});
    };

    this.deleteRoom = function(item, event) {
	$('#configRoomsTable').block({ 
            message: '<div>Please wait ...</div>', 
            css: { border: '3px solid #a00' } 
        }); 
	var content = {};
	content.uuid = item.uuid;
	content.command = 'deleteroom';
	sendCommand(content, function(res) {
	    if (res.result && res.result.returncode == 0) {
		self.rooms.remove(function(e) {
		    return e.uuid == item.uuid;
		});
		$("#configRoomsTable").dataTable().fnDeleteRow(event.target.parentNode.parentNode);
		$("#configRoomsTable").dataTable().fnDraw();
	    } else {
		alert("Error while deleting room!");
	    }
	    $('#configRoomsTable').unblock();
	});
    };

}

/**
 * Initalizes the model
 */
function init_roomConfig() {
    model = new roomConfig();

    model.mainTemplate = function() {
	return "configuration/rooms";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
