/**
 * The plugin model
 * @returns {examplePlugin}
 */
function examplePlugin() {
    this.hasNavigation = ko.observable(false);
    this.exampleText = ko.observable("Hello World");
}

/**
 * Entry point: mandatory!
 */
function init_plugin()
{
    model = new examplePlugin();
    model.mainTemplate = function() {
	return templatePath + "example";
    }.bind(model);
    ko.applyBindings(model);
}
