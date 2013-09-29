/**
 * Model class
 * 
 * @returns {systemStatus}
 */
function systemStatus(states) {
    this.hasNavigation = ko.observable(false);
    this.data = ko.observableArray([]);
    this.data(states);
}

/**
 * Initalizes the model
 */
function init_systemStatus() {
    model = new systemStatus();
    $.ajax({
	type : "GET",
	url : "/cgi-bin/system.cgi",
	success : function(result) {
	    model.data(JSON.parse(result));

	    model.mainTemplate = function() {
		return "systemStatus";
	    }.bind(model);

	    model.navigation = function() {
		return "";
	    }.bind(model);

	    ko.applyBindings(model);

	    window.setInterval(function() {
		$.ajax({
		    type : "GET",
		    url : "/cgi-bin/system.cgi",
		    success : function(res) {
			model.data(JSON.parse(res));
		    }
		});
	    }, 2000);
	},
	async : true
    });

}
