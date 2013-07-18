/**
 * Model class
 * @returns {configuration}
 */
function configuration() {
    this.hasNavigation = ko.observable(true);
}

/**
 * Initalizes the Configuration model
 */
function init_configuration() {
    model = new configuration();

    model.mainTemplate = function() {
	return "configuration";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}