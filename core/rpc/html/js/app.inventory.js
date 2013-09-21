/**
 * Model class
 * 
 * @returns {inventoryView}
 */
function inventoryView() {
    var self = this;
    this.hasNavigation = ko.observable(false);
    this.inventory = ko.observable({});
    this.data = ko.computed(function() {
	return JSON.stringify(self.inventory(), undefined, 2);
    });
}

/**
 * Initalizes the model
 */
function init_inventoryView() {
    model = new inventoryView();

    model.mainTemplate = function() {
	return "inventory";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}