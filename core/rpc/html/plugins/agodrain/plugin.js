/**
 * agodrain by jaeger@agocontrol.com
 * @returns {agodrainPlugin}
 */
function agodrainPlugin() {
    this.hasNavigation = ko.observable(true);
    this.rooms = ko.observableArray([]);

    var self = this;
    var url = "/jsonrpc";
    var subscription = "";

    this.displayEvent = function(response) {
	if (response.result) { 
		var output = document.getElementById('output');
		var content = JSON.stringify(response.result);
			output.innerHTML = '<li class="default alert">' + content + '</li>' + output.innerHTML;
	}
	self.getevent();
    };

    this.getevent = function() {
	var request = {};
	request.method = "getevent";
	request.params = {};
	request.params.uuid = subscription;
	request.id = 2;
	request.jsonrpc = "2.0";

	$.post(url, JSON.stringify(request), self.displayEvent, "json");
    };

    this.handleSubscribe = function(response) {
	if (response.result) { 
		subscription = response.result;
		var output = document.getElementById('output');
		output.innerHTML = '<br>';
		output.innerHTML = output.innerHTML + '<li class="success alert">Client subscription uuid: ' + subscription + '</li>';
		self.getevent();
	}
    };

    this.startDrain = function() {
	var request = {};
	request.method = "subscribe";
	request.id = 2;
	request.jsonrpc = "2.0";

	$.post(url, JSON.stringify(request), self.handleSubscribe, "json");
    };
}

function init_plugin()
{
    model = new agodrainPlugin();
    model.mainTemplate = function() {
	return templatePath + "agodrain";
    }.bind(model);

    model.navigation = function() {
        return templatePath + "navigation/plugins";
    }.bind(model);

    ko.applyBindings(model);
}
