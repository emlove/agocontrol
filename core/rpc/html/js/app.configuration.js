/**
 * Model class
 * @returns {configuration}
 */
function configuration() {
    this.systemvar = ko.observableArray([]);
    this.hasNavigation = ko.observable(true);

    var systemvar = {
        uuid: '164a5b03-d7d2-43de-94ea-fe2d7ac4617d',
        personAge: 123
    };
}

/**
 * Initalizes the Configuration model
 */
function init_configuration() {
    console.debug(systemvar);
    model = new configuration();

    model.mainTemplate = function() {
	return "configuration";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
