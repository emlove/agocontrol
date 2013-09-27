/**
 * Model class
 * 
 * @returns {cloudConfig}
 */
function cloudConfig() {
    this.hasNavigation = ko.observable(true);
    this.cloudURL = ko.observable("");
    this.cloudActivate = ko.observable("");

    var self = this;

    this.password = ko.observable("");
    this.passwordConfirm = ko.observable("");

    this.checkPassWords = function() {
	if (self.password() != self.passwordConfirm()) {
	    alert(document.getElementById("passwordError").innerHTML);
	    return false;
	}
	return true;
    };

    this.cloudURL("https://cloud.agocontrol.com/cloudreg/" + systemvar.uuid + "/");
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
