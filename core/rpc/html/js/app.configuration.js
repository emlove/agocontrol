/**
 * Model class
 * @returns {configuration}
 */
function configuration() {
    this.hasNavigation = ko.observable(true);
    this.systemvar = ko.observableArray([]);
    var tmp = {};
    tmp.uuid = systemvar[uuid];
    this.systemvar.push(tmp);
    console.debug(this.systemvar);
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
