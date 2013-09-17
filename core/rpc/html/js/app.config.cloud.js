/**
 * Model class
 * 
 * @returns {cloudConfig}
 */
function cloudConfig() {
    this.hasNavigation = ko.observable(true);
}

/**
 * Initalizes the cloudConfig model
 */
function init_cloudConfig() {
    model = new cloudConfig();

    model.mainTemplate = function() {
	return "configuration/cloud";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
