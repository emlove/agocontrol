/**
 * Model class
 * 
 * @returns {cloudConfig}
 */
function cloudConfig() {
    this.hasNavigation = ko.observable(true);
    this.cloudURL = ko.observable("");

    var self = this;

    this.cloudUsername = ko.observable("");
    this.cloudPassword = ko.observable("");
    this.cloudPasswordConfirm = ko.observable("");
    this.cloudPIN = ko.observable("");

    this.checkPassWords = function() {
	if (self.this.cloudPassword() != self.cloudPasswordConfirm()) {
	    alert(document.getElementById("passwordError").innerHTML);
	    return false;
	}
	return true;
    };

    this.cloudURL("https://cloud.agocontrol.com/cloudreg/" + systemvar.uuid + "/");

    /* Cloud Activation */
    self.cloudActivate = function() {
	var cloudUsername = this.cloudUsername();
	var cloudPassword = this.cloudPassword();
	var cloudPIN = this.cloudPIN();
	
	var url = "/cgi-bin/activate.cgi?action=activate&username=" + cloudUsername + "&password=" + cloudPassword + "&pin=" + cloudPIN;
	$.ajax({
		type : 'POST',
		url : url,
	});
    }
    
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
