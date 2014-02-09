/**
 * agodrain by jaeger@agocontrol.com
 * @returns {agodrainPlugin}
 */
function agodrainPlugin() {
    this.hasNavigation = ko.observable(true);
    this.rooms = ko.observableArray([]);

    var self = this;
    var _originalHandler = handleEvent;
    var subDisplayed = false;

    this.displayEvent = function(response) {
	if (response.error) {
		return;
	} else {
		if (response.result) { 
			var output = document.getElementById('output');
			var content = JSON.stringify(response.result);
			output.innerHTML = '<li class="default alert">' + content + '</li>' + output.innerHTML;
		}
		getEvent();
	}
    };

    this.stopDrain = function() {
        handleEvent = _originalHandler;
    };

    this.startDrain = function() {
	if (!self.subDisplayed) {
	    var output = document.getElementById('output');
	    output.innerHTML = '<br>';
	    output.innerHTML = output.innerHTML + '<li class="success alert">Client subscription uuid: ' + subscription + '</li>';
	    self.subDisplayed = true;
	}
	
	_originalHandler = handleEvent;
	handleEvent = self.displayEvent;
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
