/**
 * Model class
 * @returns {systemConfig}
 */
function systemConfig() {
    this.hasNavigation = ko.observable(true);
    this.system = ko.observable(systemvar);
    this.plugins = ko.observableArray([]);
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

    $.ajax({
	url: "/cgi-bin/pluginlist.cgi",
	method: "GET",
	async: true,
    }).done(function(result) {
	model.plugins(result);
    });
    
    ko.applyBindings(model);
    console.log(model.plugins());
}
