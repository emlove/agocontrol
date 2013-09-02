/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function roomConfig() {
    this.hasNavigation = ko.observable(true);
    this.rooms = ko.observableArray([]);

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
        var content = {};
        content.name = $("#roomName").val();
        content.command = 'setroomname';
        sendCommand(content, function() {
            unsubscribe();
            document.location.reload();
        });
    };

    this.deleteRoom = function(item) {
        var content = {};
        content.uuid = item.uuid;
        content.command = 'deleteroom';
        sendCommand(content, function() {
            unsubscribe();
            document.location.reload();
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
