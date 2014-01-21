infuser.defaults.templateUrl = "./templates";

Array.prototype.chunk = function(chunkSize) {
    var array = this;
    return [].concat.apply([], array.map(function(elem, i) {
	return i % chunkSize ? [] : [ array.slice(i, i + chunkSize) ];
    }));
};

if (!Date.prototype.toISOString) {
    (function() {

	function pad(number) {
	    var r = String(number);
	    if (r.length === 1) {
		r = '0' + r;
	    }
	    return r;
	}

	Date.prototype.toISOString = function() {
	    return this.getUTCFullYear() + '-' + pad(this.getUTCMonth() + 1) + '-' + pad(this.getUTCDate()) + 'T' + pad(this.getUTCHours()) + ':' + pad(this.getUTCMinutes()) + ':'
		    + pad(this.getUTCSeconds()) + '.' + String((this.getUTCMilliseconds() / 1000).toFixed(3)).slice(2, 5) + 'Z';
	};

    }());
}

ko.bindingHandlers.slider = {
    init : function(element, valueAccessor, allBindingsAccessor) {
	var options = allBindingsAccessor().sliderOptions || {};
	$(element).slider(options);
	ko.utils.registerEventHandler(element, "slidechange", function(event, ui) {
	    var observable = valueAccessor();
	    observable(ui.value);
	    // Hack to avoid setting the level on startup
	    // So we call the syncLevel method when we have
	    // a mouse event (means user triggered).
	    if (options.dev && event.clientX) {
		options.dev.syncLevel();
	    }
	});
	ko.utils.domNodeDisposal.addDisposeCallback(element, function() {
	    $(element).slider("destroy");
	});
    },
    update : function(element, valueAccessor) {
	var value = valueAccessor();
	if (isNaN(value))
	    value = 0;
	$(element).slider("value", value);
    }
};

function getPage() {
    var query = window.location.search.substring(1);
    query = query.split("&")[0];
    return query ? query : "dashboard";
}

var subscription = null;
var url = "/jsonrpc";

var schema = {};
var deviceMap = [];
var rooms = {};
var floorPlans = {};
var systemvar = {};
var variables = {};
var currentFloorPlan = ko.observable({});

var agoController = null;
var eventController = null;
var dataLoggerController = null;
var scenarioController = null;
var alertControler = null

var supported_devices = [ "switch", "dimmer", "binarysensor", "dimmerrgb", "multilevelsensor", , "scenario", "drapes", "brightnesssensor", "powermeter", "energysensor", "humiditysensor", "phone",
	"pushbutton", "placeholder", "temperaturesensor", "energymeter", "squeezebox", 'ipx800v3board' ];

function device(obj, uuid) {
    var self = this;
    for ( var k in obj) {
	this[k] = obj[k];
    }

    this.uuid = uuid;

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

    if (this.devicetype.match(/sensor$/) || this.devicetype.match(/meter$/)) {
	this.valueList = ko.computed(function() {
	    var result = [];
	    var i = 0;
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
		i++;
		if (i == 2) {
		    break;
		}
	    }
	    return result;
	});
    }

    //all mediaplayer device type
    if( this.devicetype=="squeezebox" ) {
        this.play = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'play';
            sendCommand(content);
        }

        this.pause = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'pause';
            sendCommand(content);
        }

        this.stop = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'stop';
            sendCommand(content);
        }
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
        if( el!==undefined )
            el[0].innerHTML = '';
        sendCommand(content, function(res) {
            if( el!==undefined )
            {
                if( res.result.result.error==0 )
                    color = "#00CC00";
                else
                    color = "#CC0000";
                el[0].innerHTML = '<span style="color:'+color+'">'+res.result.result.msg+'</span>';
            }
            if( callback!==null )
                callback(res);
        });
    };

    //get devices
    this.getDevices = function(callback) {
        var content = {};
        content.uuid = uuid;
        content.command = 'getdevices'
        sendCommand(content, function(res) {
            if( callback!==undefined )
                callback(res);
        });
    }

    if( this.devicetype=="ipx800controller" ) {
        self.ipx800ip = ko.observable();
        self.addboard = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'adddevice';
            content.param1 = self.ipx800ip();
            self.addDevice(content, "addboardresult", null);
        };
    }
    else if( this.devicetype=="ipx800v3board" ) {
        self.output = {};
        self.updateUi = function() {
            self.getIpx800Status();
            self.getDevices(self.getDevicesCallback);
        }
        self.getIpx800Status = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'status';
            sendCommand(content, function(res) {
                el = document.getElementsByClassName("currentoutputs");
                el[0].innerHTML = res.result.result.outputs
                el = document.getElementsByClassName("currentanalogs");
                el[0].innerHTML = res.result.result.analogs
                el = document.getElementsByClassName("currentcounters");
                el[0].innerHTML = res.result.result.counters
            });
        }
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
            if( newVal=="switch" )
            {
                self.devswitch(true);
                self.devdrapes(false);
            }
            else if( newVal=="drapes" )
            {
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
            if( content.type=="switch" )
                content.param1 = self.selectedOutputParam1();
            else if( content.type=="drapes")
            {
                content.param1 = self.selectedOutputParam1();
                content.param2 = self.selectedOutputParam2();
            }
            self.addDevice(content, "addoutputresult", self.getIpx800Status);
        }
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
            content.type = 'counter'
            content.param1 = self.selectedCounterParam1();
            self.addDevice(content, "addcounterresult", self.getIpx800Status);
        };
        self.devices = ko.observableArray([]);
        self.getDevicesCallback = function(res) {
            self.devices(res.result.result.devices);
        }
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
        }
    }
    else if (this.devicetype == "alertcontroller") {
    	alertController = uuid;
        self.gtalkStatus = ko.observable(self.gtalkStatus);
        self.gtalkUsername = ko.observable(self.gtalkUsername);
        self.gtalkPassword = ko.observable(self.gtalkPassword);
        self.smsStatus = ko.observable(self.smsStatus);
        self.twelvevoipUsername = ko.observable(self.twelvevoipUsername);
        self.twelvevoipPassword = ko.observable(self.twelvevoipPassword);
        self.mailStatus = ko.observable(self.mailStatus);
        self.mailSmtp = ko.observable(self.mailSmtp);
        self.mailSender = ko.observable(self.mailSender);
        self.twitterStatus = ko.observable(self.twitterStatus);
        self.pushStatus = ko.observable(self.pushStatus);
        self.selectedPushProvider = ko.observable(self.selectedPushProvider);
        self.pushbulletSelectedDevices = ko.observableArray();
        self.pushbulletAvailableDevices = ko.observableArray();
        self.pushbulletApikey = ko.observable();
        self.pushoverUserid = ko.observable();
        self.nmaApikey = ko.observable(self.nmaApikey);
        self.nmaAvailableApikeys = ko.observableArray();
        self.nmaSelectedApikeys = ko.observableArray();

        //get current status
        self.getAlertsConfigs = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'status';
            sendCommand(content, function(res) {
                self.gtalkStatus(true);
                if( res.result.result.gtalk.configured )
                {
                    self.gtalkUsername(res.result.result.gtalk.username);
                    self.gtalkPassword(res.result.result.gtalk.password);
                }
                self.mailStatus(res.result.result.mail.configured);
                if( res.result.result.mail.configured )
                {
                    self.mailSmtp(res.result.result.mail.smtp);
                    self.mailSender(res.result.result.mail.sender);
                }
                self.smsStatus(res.result.result.sms.configured);
                if( res.result.result.sms.configured )
                {
                    self.twelvevoipUsername(res.result.result.sms.username);
                    self.twelvevoipPassword(res.result.result.sms.password);
                }
                self.twitterStatus(res.result.result.twitter.configured);
                self.pushStatus(res.result.result.push.configured);
                if( res.result.result.push.configured )
                {
                    self.selectedPushProvider(res.result.result.push.provider);
                    if( res.result.result.push.provider=='pushbullet' )
                    {
                        self.pushbulletApikey(res.result.result.push.apikey);
                        self.pushbulletAvailableDevices(res.result.result.push.devices);
                        self.pushbulletSelectedDevices(res.result.result.push.devices);
                    }
                    else if( res.result.result.push.provider=='pushover' )
                    {    
                        self.pushoverUserid(res.result.result.push.userid);
                    }
                    else if( res.result.result.push.provider=='notifymyandroid' )
                    {
                        self.nmaAvailableApikeys(res.result.result.push.apikeys);
                    }
                }
            });
        }
        self.dialogopened = function(dialog) {
            $("#tabs").tabs({
                beforeActivate: function(event,ui) {
                    console.log('-> selected tab index: '+ui.newTab.index());
                }
            });
            self.getAlertsConfigs();
        };
        this.twitterUrl = function() {
            el = document.getElementsByClassName("twitterUrl");
            el[0].innerHTML = 'Generating url...';
            //get authorization url
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'twitter';
            content.param2 = '';
            sendCommand(content, function(res) {
                if( res.result.result.error==0 )
                {
                    //display link
                    el[0].innerHTML = '<a href="'+res.result.result.url+'" target="_blank">authorization url</a>';
                }
                else
                {
                    alert('Unable to get Twitter url.');
                }
            });
        }
        this.twitterAccessCode = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'twitter';
            content.param2 = document.getElementsByClassName("twitterCode")[0].value;
            sendCommand(content, function(res) {
                if( res.result.result.error==1 )
                {
                    alert(res.result.result.msg);
                }
                self.getAlertsConfigs();
            });
        }
        this.twitterTest = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'test';
            content.param1 = 'twitter'
            sendCommand(content, function(res) {
                alert( res.result.result.msg );
            });
        }
        this.smsConfig = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'sms'
            content.param2 = self.smsUsername();
            content.param3 = self.smsPassword();
            sendCommand(content, function(res) {
                if( res.result.result.error==1 )
                {
                    alert(res.result.result.msg);
                }
                self.getAlertsConfigs();
            });
        }
        this.smsTest = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'test';
            content.param1 = 'sms'
            sendCommand(content, function(res) {
                alert( res.result.result.msg );
            });
        }
        this.gtalkConfig = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'gtalk'
            content.param2 = self.gtalkUsername();
            content.param3 = self.gtalkPassword();
            sendCommand(content, function(res) {
                if( res.result.result.error==1 )
                {
                    alert(res.result.result.msg);
                }
                self.getAlertsConfigs();
            });
        }
        this.gtalkTest = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'test';
            content.param1 = 'gtalk';
            sendCommand(content, function(res) {
                if( res.result.result.error==1 )
                {
                    alert( res.result.result.msg );
                }
            });
        }
        this.mailConfig = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'mail'
            content.param2 = self.mailSmtp();
            content.param3 = self.mailSender();
            sendCommand(content, function(res) {
                if( res.result.result.error==1 )
                {
                    alert(res.result.result.msg);
                }
                self.getAlertsConfigs();
            });
        }
        this.mailTest = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'test';
            content.param1 = 'mail';
            content.param2 = document.getElementsByClassName("mailEmail")[0].value;
            sendCommand(content, function(res) {
                alert( res.result.result.msg );
            });
        }
        this.pushbulletRefreshDevices = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'push';
            content.param2 = this.selectedPushProvider();
            content.param3 = 'getdevices';
            content.param4 = self.pushbulletApikey();
            sendCommand(content, function(res) {
                if( res.result.result.error==0 )
                {
                    self.pushbulletAvailableDevices(res.result.result.devices);
                }
                else
                {
                    //TODO error
                }
            });
        }
        this.nmaAddApikey = function() {
            if( self.nmaApikey().length>0 )
            {
                self.nmaAvailableApikeys.push(self.nmaApikey());
            }
            self.nmaApikey('');
        }
        this.nmaDelApikey = function() {
            for(var j=self.nmaSelectedApikeys().length-1; j>=0; j--)
            {
                for(var i=self.nmaAvailableApikeys().length-1; i>=0; i--)
                {
                    if( self.nmaAvailableApikeys()[i]===self.nmaSelectedApikeys()[j] )
                        self.nmaAvailableApikeys().splice(i, 1);
                }
            }
            self.nmaAvailableApikeys(self.nmaAvailableApikeys());
        }
        this.pushConfig = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'setconfig';
            content.param1 = 'push';
            content.param2 = this.selectedPushProvider();
            if( this.selectedPushProvider()=='pushbullet' )
            {
                content.param3 = 'save';
                content.param4 = this.pushbulletApikey();
                content.param5 = this.pushbulletSelectedDevices();
            }
            else if( this.selectedPushProvider()=='pushover' )
            {
                content.param3 = this.pushoverUserid();
            }
            else if( this.selectedPushProvider()=='notifymyandroid' )
            {
                content.param3 = this.nmaAvailableApikeys();
            }
            sendCommand(content, function(res) {
                if( res.result.result.error==1 )
                    alert( res.result.result.msg );
                self.getAlertsConfigs();
            });
        }
        this.pushTest = function() {
            var content = {};
            content.uuid = uuid;
            content.command = 'test';
            content.param1 = 'push';
            sendCommand(content, function(res) {
                alert( res.result.result.msg );
            });
        }
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

function buildfloorPlanList(model) {
    model.floorPlans = ko.observableArray([]);
    for ( var k in floorPlans) {
	model.floorPlans.push({
	    uuid : k,
	    name : floorPlans[k].name
	});
    }
}

/**
 * This gets set when the GUI needs to be initalized after loading the
 * inventory.
 */
var deferredInit = null;

function initGUI() {
    var page = getPage();
    if (page == "dashboard") {
	deferredInit = init_dashBoard;
    } else if (page == "floorplan") {
	deferredInit = init_floorPlan;
    } else if (page == "roomConfig") {
	init_roomConfig();
    } else if (page == "variablesConfig") {
	init_variablesConfig();
    } else if (page == "floorplanConfig") {
	init_floorplanConfig();
    } else if (page == "configuration") {
	deferredInit = init_configuration;
    } else if (page == "cloudConfig") {
	deferredInit = init_cloudConfig;
    } else if (page == "deviceConfig") {
	init_deviceConfig();
    } else if (page == "systemConfig") {
	deferredInit = init_systemConfig;
    } else if (page == "eventConfig") {
	init_eventConfig();
    } else if (page == "scenarioConfig") {
	init_scenarioConfig();
    } else if (page == "inventoryView") {
	deferredInit = init_inventoryView;
    } else if (page == "systemStatus") {
	init_systemStatus();
    }
}

initGUI();

// --- AGO --- //

function handleEvent(response) {
    for ( var i = 0; i < deviceMap.length; i++) {
	if (deviceMap[i].uuid == response.result.uuid && response.result.level !== undefined) {
	    deviceMap[i].state(parseInt(response.result.level));
	    deviceMap[i].timeStamp(formatDate(new Date()));
	    if (response.result.quantity) {
		var values = deviceMap[i].values();
		/* We have no values so reload from inventory */
		if (values[response.result.quantity] === undefined) {
		    var content = {};
		    content.command = "inventory";
		    sendCommand(content, function(inv) {
			var tmpInv = cleanInventory(inv.result.devices);
			if (tmpInv[response.result.uuid] !== undefined) {
			    if (tmpInv[response.result.uuid].values) {
				deviceMap[i].values(tmpInv[response.result.uuid].values);
			    }
			}
		    });
		    break;
		}
		values[response.result.quantity].level = response.result.level;
		deviceMap[i].values(values);
	    }

	    break;
	}

    }
    getEvent();
}

function getEvent() {
    var request = {};
    request.method = "getevent";
    request.params = {};
    request.params.uuid = subscription;
    request.id = 1;
    request.jsonrpc = "2.0";

    $.post(url, JSON.stringify(request), handleEvent, "json");
}

function cleanInventory(data) {
    for ( var k in data) {
	if (!data[k]) {
	    delete data[k];
	}
    }

    return data;
}

function handleInventory(response) {
    rooms = response.result.rooms;
    systemvar = response.result.system;
    schema = response.result.schema;
    floorPlans = response.result.floorplans;
    variables = response.result.variables;

    /* Parse floorplan uuid */
    var fp = window.location.search.substring(1);
    var tmp = fp.split("&");
    for ( var i = 0; i < tmp.length; i++) {
	if (tmp[i].indexOf("fp=") == 0) {
	    fp = tmp[i].split("=")[1];
	}
    }

    for ( var k in floorPlans) {
	if (k == fp) {
	    var tmp;
	    tmp = floorPlans[k];
	    tmp.uuid = k;
	    currentFloorPlan(tmp);
	}
    }

    var inventory = cleanInventory(response.result.devices);
    for ( var uuid in inventory) {
	if (inventory[uuid].room !== undefined && inventory[uuid].room) {
	    inventory[uuid].roomUID = inventory[uuid].room;
	    if (rooms[inventory[uuid].room] !== undefined) {
		inventory[uuid].room = rooms[inventory[uuid].room].name;
	    } else {
		inventory[uuid].room = "";
	    }

	} else {
	    inventory[uuid].room = "";
	}
	deviceMap.push(new device(inventory[uuid], uuid));
    }

    if (deferredInit) {
	deferredInit();
    }

    if (model.devices !== undefined) {
	model.devices(deviceMap);
    }

    if (model.inventory !== undefined) {
	model.inventory(response.result);
    }

    if (model.rooms !== undefined && model.rooms.slice !== undefined) {
	/* get uuid into rooms */
	model.rooms([]);
	for ( var uuid in rooms) {
	    var tmp = rooms[uuid];
	    tmp.uuid = uuid;
	    model.rooms.push(tmp);
	}
    }
    if (model.floorplans !== undefined) {
	/* get uuid into floorplans */
	model.floorplans([]);
	for ( var uuid in floorPlans) {
	    var tmp = floorPlans[uuid];
	    tmp.uuid = uuid;
	    model.floorplans.push(tmp);
	}
    }

    if (model.variables !== undefined) {
	model.variables([]);
	for ( var key in variables) {
	    var tmp = {};
	    tmp.variable = key;
	    tmp.value = variables[key];
	    model.variables.push(tmp);
	}
    }
}

function getInventory() {
    var content = {};
    content.command = "inventory";
    sendCommand(content, handleInventory);
}

function unsubscribe() {
    var request = {};
    request.method = "unsubscribe";
    request.id = 1;
    request.jsonrpc = "2.0";
    request.params = {};
    request.params.uuid = subscription;

    $.post(url, JSON.stringify(request), function() {
    }, "json");
}

function handleSubscribe(response) {
    if (response.result) {
	subscription = response.result;
	getInventory();
	getEvent();
	window.onbeforeunload = function(event) {
	    unsubscribe();
	};
    }
}

function sendCommand(content, callback, timeout) {
    var request = {};
    request.method = "message";
    request.params = {};
    request.params.content = content;
    if (timeout) {
	request.params.replytimeout = timeout;
    }
    request.id = 1;
    request.jsonrpc = "2.0";

    $.ajax({
	type : 'POST',
	url : url,
	data : JSON.stringify(request),
	success : function(r) {
	    if (callback !== undefined) {
		callback(r);
	    }
	},
	dataType : "json",
	async : true
    });
}

function subscribe() {
    var request = {};
    request.method = "subscribe";
    request.id = 1;
    request.jsonrpc = "2.0";

    $.post(url, JSON.stringify(request), handleSubscribe, "json");
}

subscribe();

$(function() {
    $("#colorPickerDialog").dialog({
	autoOpen : false,
	modal : true,
	minHeight : 300,
	minWidth : 300,
	buttons : {
	    Cancel : function() {
		$(this).dialog("close");
	    },
	    OK : function() {
		var content = {};
		content.uuid = $("#colorPickerDialog").data('uuid');
		content.command = "setcolor";
		var color = $('#colorValue').val();
		content.red = parseInt(color.substring(0, 2), 16);
		content.green = parseInt(color.substring(2, 4), 16);
		content.blue = parseInt(color.substring(4, 6), 16);
		sendCommand(content);
		$(this).dialog("close");
	    }
	}
    });
});

/* Opens color picker */
function openColorPicker(uuid) {
    $("#colorPickerDialog").data('uuid', uuid);
    $("#colorPickerDialog").dialog("open");
}

/**
 * Opens details page for the given device
 * 
 * @param device
 * @param environment
 */
function showDetails(device, environment) {
    /* Check if we have a template if yes use it otherwise fall back to default */
    $.ajax({
	type : 'HEAD',
	url : "templates/details/" + device.devicetype + ".html",
	success : function() {
	    doShowDetails(device, device.devicetype, environment);
	},
	error : function() {
	    doShowDetails(device, "default");
	}
    });
}

/**
 * Formats a date object
 * 
 * @param date
 * @param simple
 * @returns {String}
 */
function formatDate(date) {
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
};

/**
 * Shows the command selector for the detail pages
 * 
 * @param container
 * @param device
 */
function showCommandList(container, device) {
    var commandSelect = document.createElement("select");
    var commandParams = document.createElement("span");
    commandSelect.id = "commandSelect";
    var type = device.devicetype;
    for ( var i = 0; i < schema.devicetypes[type].commands.length; i++) {
	commandSelect.options[i] = new Option(schema.commands[schema.devicetypes[type].commands[i]].name, schema.devicetypes[type].commands[i]);
    }

    commandSelect.onchange = function() {
    	if (commandSelect.options.length == 0) {
    	    return 0;
	    }
    	var cmd = schema.commands[commandSelect.options[commandSelect.selectedIndex].value];
	    commandParams.innerHTML = "";
    	if (cmd.parameters !== undefined)
        {
	        commandParams.style.display = "";
    	    for ( var param in cmd.parameters)
            {
                if( cmd.parameters[param].type=='option' )
                {
                    var select = document.createElement("select");
                    select.name = param;
                    select.className = "cmdParam";
                    for( var i=0; i<cmd.parameters[param].options.length; i++ )
                        select.options[select.options.length] = new Option(cmd.parameters[param].options[i], cmd.parameters[param].options[i]);
    	    	    commandParams.appendChild(select);
                }
                else
                {
        	    	var input = document.createElement("input");
        	    	input.name = param;
	        	    input.className = "cmdParam";
    	        	input.placeholder = cmd.parameters[param].name;
    	    	    commandParams.appendChild(input);
                }
	        }
    	}
        else
        {
	        commandParams.style.display = "none";
    	}
    };

    commandSelect.onchange();

    container.appendChild(commandSelect);
    container.appendChild(commandParams);
}

/**
 * Shows the detail page of a device
 * 
 * @param device
 * @param template
 * @param environment
 */
function doShowDetails(device, template, environment) {
    ko.renderTemplate("details/" + template, device, {
	afterRender : function() {
	    var dialogWidth = 800;
	    var dialogHeight = 300;

	    if (document.getElementById('commandList')) {
		showCommandList(document.getElementById('commandList'), device);
	    }

	    if (device.devicetype == "camera") {
		dialogHeight = 620;
		device.getVideoFrame();
	    }

	    if (document.getElementById('graph') && ((device.valueList && device.valueList() && device.valueList().length) || device.devicetype == "binarysensor")) {
		/* Setup start date */
		var start = new Date((new Date()).getTime() - 24 * 3600 * 1000);
		$("#start_date").datepicker({
		    dateFormat : "dd.mm.yy",
		    onSelect : function() {
			renderGraph(device, document.getElementById('graph')._environment);
		    }
		});
		$("#start_date").datepicker("setDate", start);

		/* Setup end date */
		$("#end_date").datepicker({
		    dateFormat : "dd.mm.yy",
		    onSelect : function() {
			renderGraph(device, document.getElementById('graph')._environment);
		    }
		});
		$("#end_date").datepicker("setDate", new Date());

		if (device.devicetype == "binarysensor") {
		    environment = "device.state";
		}

		renderGraph(device, environment ? environment : device.valueList()[0].name);

		document.getElementsByName("displayType")[0].onchange = function() {
		    renderGraph(device, environment ? environment : device.valueList()[0].name);
		};

		document.getElementsByName("displayType")[1].onchange = function() {
		    renderGraph(device, environment ? environment : device.valueList()[0].name);
		};

		dialogWidth = 1000;
		dialogHeight = 720;
	    }

        //detail dialog size
        if( device.devicetype=="alertcontroller" )
        {
            dialogWidth = 800;
            dialogHeight = 625;
        }
        else if( device.devicetype=="ipx800controller" )
        {
            dialogWidth = 800;
            dialogHeight = 325;
        }
        else if( device.devicetype=="ipx800v3board" )
        {
            dialogWidth = 800;
            dialogHeight = 600;
        }

	    if (document.getElementById("detailsTitle")) {
		$("#detailsPage").dialog({
		    title : document.getElementById("detailsTitle").innerHTML,
		    modal : true,
		    width : dialogWidth,
		    height : dialogHeight,
		    close : function() {
			var graphContainer = document.getElementById('graph');
			if (graphContainer) {
			    graphContainer.parentNode.removeChild(graphContainer);
			}
		    },
		    open : function() {
			    $("#detailsPage").css("overflow", "visible");
                if( device.dialogopened!==undefined )
                    device.dialogopened(this);
		    }
		});
	    }

	}
    }, document.getElementById("detailsPage"));
}

/**
 * Renders the graph for the given device and environment
 * 
 * @param device
 * @param environment
 */
function renderGraph(device, environment) {

    var renderType = $($('input[name="displayType"]:checked')[0]).val();

    $('#graph').show();
    $('#dataList').hide();

    $('#graph').block({
	message : '<div>Please wait ...</div>',
	css : {
	    border : '3px solid #a00'
	}
    });

    var max_ticks = 25; // User option?

    var endDate = new Date($("#end_date").datepicker("getDate").getTime() + 1000 * 3600 * 23 + 60 * 59);

    var content = {};
    content.uuid = dataLoggerController;
    content.command = "getdata";
    content.deviceid = device.uuid;
    content.start = $("#start_date").datepicker("getDate").toISOString();
    content.end = endDate.toISOString();
    content.env = environment.toLowerCase();

    sendCommand(content, function(res) {
	if (!res.result || !res.result.result || !res.result.result.values) {
	    alert("Error while loading Graph!");
	    $('#graph').unblock();
	    return;
	}

	/* Get the unit */
	var unit = "";
	for ( var k = 0; k < device.valueList().length; k++) {
	    if (device.valueList()[k].name == environment) {
		unit = device.valueList()[k].unit;
		break;
	    }
	}

	/* Prepare the data */
	var data = [];
	var values = res.result.result.values;

	if (renderType == "list") {
	    values.sort(function(a, b) {
		return b.time - a.time;
	    });

	    for ( var i = 0; i < values.length; i++) {
		values[i].date = formatDate(new Date(values[i].time * 1000));
		values[i].value = values[i].level + " " + unit;
		delete values[i].level;
	    }

	    ko.renderTemplate("details/datalist", {
		data : values,
		environment : environment
	    }, {}, document.getElementById("dataList"));
	    $('#graph').unblock();
	    $("#graph").hide();
	    $('#dataList').show();
	    return;
	}

	/* Split the values into buckets */
	var num_buckets = Math.max(1, Math.floor(values.length / max_ticks));
	var buckets = values.chunk(num_buckets);
	var labels = [];
	var i = 0;

	/*
	 * Compute averange for each bucket and pick a representative time to
	 * display
	 */
	for ( var j = 0; j < buckets.length; j++) {
	    var bucket = buckets[j];
	    var ts = bucket[0].time + (bucket[bucket.length - 1].time - bucket[0].time) / 2;
	    labels.push(new Date(Math.floor(ts) * 1000));
	    var value = 0;
	    for ( var k = 0; k < bucket.length; k++) {
		value += bucket[k].level;
	    }
	    data.push([ i, value / k ]);
	    i++;
	}

	/* Render the graph */
	var container = document.getElementById('graph');
	container._environment = environment;
	Flotr.draw(container, [ data ], {
	    HtmlText : false,
	    title : environment,
	    mode : "time",
	    yaxis : {
		tickFormatter : function(x) {
		    return x + " " + unit;
		},
	    },
	    mouse : {
		track : true,
		relative : true,

		trackFormatter : function(o) {
		    return formatDate(labels[Math.round(o.x)]) + " - " + o.y + " " + unit;
		}
	    },
	    xaxis : {
		noTicks : i,
		labelsAngle : 90,
		tickDecimals : 0,
		tickFormatter : function(x) {
		    return formatDate(labels[x]);
		}
	    }
	});

	/* We have no data ... */
	if (data.length == 0) {
	    var canvas = document.getElementsByClassName("flotr-overlay")[0];
	    var context = canvas.getContext("2d");
	    var x = canvas.width / 2;
	    var y = canvas.height / 2;

	    context.font = "30pt Arial";
	    context.textAlign = "center";
	    context.fillStyle = "red";
	    context.fillText('No data found for given time frame!', x, y);
	}

	$('#graph').unblock();
    }, 30);
}
