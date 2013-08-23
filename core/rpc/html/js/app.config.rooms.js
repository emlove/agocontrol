/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function roomConfig() {
    this.rooms = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);
    /* get uuid into rooms */
    for (var uuid in rooms) { var tmp = rooms[uuid]; tmp.uuid = uuid; this.rooms.push(tmp); }
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
