/**
 * Model class
 * 
 * @returns {roomConfig}
 */
function roomConfig() {
    this.rooms = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);

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
