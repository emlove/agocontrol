/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function roomConfig() {
    this.hasNavigation = ko.observable(true);
    this.rooms = ko.observableArray([]);

    /* get uuid into rooms */
    for (var uuid in rooms) { var tmp = rooms[uuid]; tmp.uuid = uuid; this.rooms.push(tmp); }

    this.makeEditableRooms = function() {
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
