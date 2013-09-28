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
	var buttons = {};
	var closeButton = $("#closeButton").data("close"); 

	buttons[closeButton] = function() {
		$(self.openDialog).dialog("close");
		self.openDialog = null;
	};
	
	var url = "/cgi-bin/activate.cgi?action=activate&username=" + cloudUsername + "&password=" + cloudPassword + "&pin=" + cloudPIN;
	$.ajax({
		type : 'POST',
		url : url,
		success : function(res) {
			var result = JSON.parse(res);
			self.openDialog = "#cloudActivationResult_" + result.rc;
			if (document.getElementById("cloudActivationResultTitle")) {
				$(self.openDialog).dialog({
					title : document.getElementById("cloudActivationResultTitle").innerHTML,
					modal: true,
					height: 180,
					width: 500,
					buttons: buttons
				});
			}
		},
		async: true
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
