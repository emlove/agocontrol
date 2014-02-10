/**
 * Model class
 * @returns {pluginsConfig}
 */
function pluginsConfig() {
    this.hasNavigation = ko.observable(true);
    this.plugins = ko.observableArray([]);
}

/**
 * Initalizes the System model
 */
function init_pluginsConfig() {
    model = new pluginsConfig();

    model.mainTemplate = function() {
	return "configuration/plugins";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    $.ajax({
	url: "/cgi-bin/pluginlist.cgi",
	method: "GET",
	async: true,
    }).done(function(result) {
	model.plugins(result);
    });
    
    ko.applyBindings(model);
}
