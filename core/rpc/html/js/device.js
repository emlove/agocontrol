/**
 * Device class used by app.js and others for representing and interaction
 * with devices
 * 
 * @param obj
 * @param uuid
 * @returns {device}
 */
function device(obj, uuid) {
    var self = this;
    for ( var k in obj) {
	this[k] = obj[k];
    }

    this.uuid = uuid;

    this.action = ''; // dummy for table
    
    this.handledBy = this['handled-by'];

    var currentState = parseInt(this.state);
    this.state = ko.observable(currentState);

    this.values = ko.observable(this.values);

    this.timeStamp = ko.observable(formatDate(new Date(this.lastseen * 1000)));

    if (this.devicetype == "dimmer" || this.devicetype == "dimmerrgb") {
	this.level = ko.observable(currentState);
	this.syncLevel = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = "setlevel";
	    content.level = self.level();
	    sendCommand(content);
	};
    }

    if (this.devicetype == "dataloggercontroller") {
	dataLoggerController = uuid;
    }

    if (this.devicetype == "agocontroller") {
	agoController = uuid;
    }

    if (this.devicetype == "eventcontroller") {
	eventController = uuid;
    }

    if (this.devicetype == "scenariocontroller") {
	scenarioController = uuid;
    }

    if (this.devicetype == "dimmerrgb") {
	this.setColor = function() {
	    openColorPicker(uuid);
	};
    }

    if (this.devicetype.match(/sensor$/) || this.devicetype.match(/meter$/) || this.devicetype.match(/thermostat$/)) {
	this.valueList = ko.computed(function() {
	    var result = [];
	    // var i = 0;
	    for ( var k in self.values()) {
		var unit = self.values()[k].unit;
		if (schema.units[self.values()[k].unit] !== undefined) {
		    unit = schema.units[self.values()[k].unit].label;
		}
		result.push({
		    name : k.charAt(0).toUpperCase() + k.substr(1),
		    level : self.values()[k].level,
		    unit : unit
		});
		// i++;
		// if (i == 2) {
		//    break;
		//}
	    }
	    return result;
	});
    }

    //TODO add here other mediaplayer type
    if (this.devicetype == "squeezebox") {
	this.mediastate = ko.observable(''); //string variable

	this.play = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'play';
	    sendCommand(content);
	};

	this.pause = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'pause';
	    sendCommand(content);
	};

	this.stop = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'stop';
	    sendCommand(content);
	};
    }

    this.allOn = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'allon';
	sendCommand(content);
    };

    this.allOff = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'alloff';
	sendCommand(content);
    };

    this.turnOn = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'on';
	sendCommand(content);
    };

    this.turnOff = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'off';
	sendCommand(content);
    };

    this.turnStop = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'stop';
	sendCommand(content);
    };

    this.turnPush = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'push';
	sendCommand(content);
    };

    this.reset = function() {
	var content = {};
	content.uuid = uuid;
	content.command = 'reset';
	sendCommand(content);
    };

    this.customCommand = function(params) {
	var content = {};
	content.uuid = uuid;
	for ( var key in params) {
	    if (params.hasOwnProperty(key)) {
		content[key] = params[key];
	    }
	}
	sendCommand(content);
    };

    this.execCommand = function() {
	var command = document.getElementById("commandSelect").options[document.getElementById("commandSelect").selectedIndex].value;
	var content = {};
	content.uuid = uuid;
	content.command = command;
	var params = document.getElementsByClassName("cmdParam");
	for ( var i = 0; i < params.length; i++) {
	    content[params[i].name] = params[i].value;
	}
	sendCommand(content, function(res) {
	    alert("Done");
	});
    };

    //add device function
    this.addDevice = function(content, containername, callback) {
	var el = document.getElementsByClassName(containername);
	if (el !== undefined)
	    el[0].innerHTML = '';
	sendCommand(content, function(res) {
	    if (el !== undefined) {
		if (res.result.result.error == 0)
		    color = "#00CC00";
		else
		    color = "#CC0000";
		el[0].innerHTML = '<span style="color:' + color + '">' + res.result.result.msg + '</span>';
	    }
	    if (callback !== null)
		callback(res);
	});
    };

    //get devices
    this.getDevices = function(callback) {
	var content = {};
	content.uuid = uuid;
	content.command = 'getdevices';
	sendCommand(content, function(res) {
	    if (callback !== undefined)
		callback(res);
	});
    };

    if (this.devicetype == "ipx800controller") {
	self.ipx800ip = ko.observable();
	self.addboard = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'adddevice';
	    content.param1 = self.ipx800ip();
	    self.addDevice(content, "addboardresult", null);
	};
    } else if (this.devicetype == "ipx800v3board") {
	self.output = {};
	self.updateUi = function() {
	    self.getIpx800Status();
	    self.getDevices(self.getDevicesCallback);
	};

	self.getIpx800Status = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'status';
	    sendCommand(content, function(res) {
		el = document.getElementsByClassName("currentoutputs");
		el[0].innerHTML = res.result.result.outputs;
		el = document.getElementsByClassName("currentanalogs");
		el[0].innerHTML = res.result.result.analogs;
		el = document.getElementsByClassName("currentcounters");
		el[0].innerHTML = res.result.result.counters;
	    });
	};

	self.dialogopened = function(dialog) {
	    $("#tabs").tabs();
	    self.updateUi();
	};
	self.devswitch = ko.observable(true);
	self.devdrapes = ko.observable(false);
	self.selectedOutputParam1 = ko.observable();
	self.selectedOutputParam2 = ko.observable();
	self.selectedAnalogParam1 = ko.observable();
	self.selectedCounterParam1 = ko.observable();
	self.selectedOutputType = ko.observable();
	self.selectedOutputType.subscribe(function(newVal) {
	    if (newVal == "switch") {
		self.devswitch(true);
		self.devdrapes(false);
	    } else if (newVal == "drapes") {
		self.devswitch(false);
		self.devdrapes(true);
	    }
	});
	self.selectedAnalogType = ko.observable();
	self.addoutput = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'adddevice';
	    content.type = self.selectedOutputType();
	    if (content.type == "switch")
		content.param1 = self.selectedOutputParam1();
	    else if (content.type == "drapes") {
		content.param1 = self.selectedOutputParam1();
		content.param2 = self.selectedOutputParam2();
	    }
	    self.addDevice(content, "addoutputresult", self.getIpx800Status);
	};

	self.addanalog = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'adddevice';
	    content.type = self.selectedAnalogType();
	    content.param1 = self.selectedAnalogParam1();
	    self.addDevice(content, "addanalogresult", self.getIpx800Status);
	};

	self.addcounter = function() {
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'adddevice';
	    content.type = 'counter';
	    content.param1 = self.selectedCounterParam1();
	    self.addDevice(content, "addcounterresult", self.getIpx800Status);
	};

	self.devices = ko.observableArray([]);
	self.getDevicesCallback = function(res) {
	    self.devices(res.result.result.devices);
	};

	self.selectedDevice = ko.observable();
	self.selectedDeviceState = ko.observable();
	self.forcestateresult = ko.observable();
	self.forcestate = function() {
	    self.forcestateresult("");
	    var content = {};
	    content.uuid = uuid;
	    content.command = 'forcestate';
	    content.state = self.selectedDeviceState();
	    content.device = self.selectedDevice();
	    sendCommand(content, function(res) {
		self.forcestateresult(res.result.result.msg);
	    });
	};
    }

    if (this.devicetype == "camera") {
	this.getVideoFrame = function() {
	    var content = {};
	    content.command = "getvideoframe";
	    content.uuid = self.uuid;
	    sendCommand(content, function(r) {
		console.log(r);
		if (r.result.image && document.getElementById("camIMG")) {
		    document.getElementById("camIMG").src = "data:image/jpeg;base64," + r.result.image;
		    $("#camIMG").show();
		}
	    }, 90);
	};
    }

}
