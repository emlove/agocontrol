/**
 * Model class
 * @returns {systemConfig}
 */
function systemConfig() {
    this.hasNavigation = ko.observable(true);
    this.system = ko.observable(systemvar);
}

/**
 * Initalizes the System model
 */
function init_systemConfig() {
    model = new systemConfig();

    model.mainTemplate = function() {
	return "configuration/system";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
