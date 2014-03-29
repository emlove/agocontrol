/**
 * @info Blocky for agocontrol
 * @info tanguy.bonneau@gmail.com
 * @see block builder: https://blockly-demo.appspot.com/static/apps/blockfactory/index.html
 */

'use strict';

//====================================
//AGOCONTROL OBJECT
//====================================
window.BlocklyAgocontrol = {
    schema: {},
    devices: [],
    variables: [],

    //init
    init: function(schema, devices, variables) {
        this.schema = schema;
        this.devices = devices;
        //only variable names are useful
        for( var variable in variables )
        {
            this.variables.push(variable);
        }
    },

    //shorten event name to not overload block
    shortenedEvent: function(event) {
        var out = event.replace("event.", "");
        out = out.replace("environment", "env");
        out = out.replace("device", "dev");
        out = out.replace("mediaplayer", "mplay");
        out = out.replace("proximity", "prox");
        out = out.replace("telecom", "tel");
        out = out.replace("security", "sec");
        return out;
    },

    //get devices
    getDevices: function(deviceType) {
        var devices = [];
        var device;
        for( var i=0; i<this.devices.length; i++ )
        {
            device = this.devices[i];
            if( device.name.length>0 && device.devicetype==deviceType )
            {
                devices.push([device.name, device.uuid]);
            }
        }
        //prevent from js crash
        if( devices.length===0 )
            devices.push(['', '']);
        return devices;
    },

    //get device types
    getDeviceTypes: function() {
        var types = [];
        var duplicates = [];
        var device;
        for( var i=0; i<this.devices.length; i++ )
        {
            device = this.devices[i];
            if( device.name.length>0 && duplicates.indexOf(device.devicetype)==-1 )
            {
                types.push([device.devicetype, device.devicetype]);
                duplicates.push(device.devicetype);
            }
        }
        //prevent from js crash
        if( types.length===0 )
            types.push(['', '']);
        return types;
    },

    //get all events
    getAllEvents: function() {
        var events = [];
        for( var event in this.schema.events )
        {
            if( event!==undefined )
                events.push([this.shortenedEvent(event), event]);
        }
        //prevent from js crash
        if( events.length===0 )
            events.push(['', '']);
        return events;
    },

    //get device events
    getDeviceEvents: function(deviceType) {
        var events = [];
        if( this.schema.devicetypes[deviceType]!==undefined && this.schema.devicetypes[deviceType].events!==undefined )
        {
            for( var i=0; i<this.schema.devicetypes[deviceType].events.length; i++ )
            {
                events.push([this.shortenedEvent(this.schema.devicetypes[deviceType].events[i]), this.schema.devicetypes[deviceType].events[i]]);
            }
        }
        //prevent from js crash
        if( events.length===0 )
            events.push(['', '']);
        return events;
    },

    //get event properties
    getEventProperties: function(event) {
        var props = [];
        if( this.schema.events[event]!==undefined && this.schema.events[event].parameters )
        {
            for( var i=0; i<this.schema.events[event].parameters.length; i++ )
            {
                props.push([this.schema.events[event].parameters[i], this.schema.events[event].parameters[i]]);
            }
        }
        //prevent from js crash
        if( props.length===0 )
            props.push(['', '']);
        return props;
    },

    //get device properties
    getDeviceProperties: function(deviceType) {
        var props = {};
        if( this.schema.devicetypes[deviceType]!==undefined && this.schema.devicetypes[deviceType].properties!==undefined )
        {
            var prop;
            for( var i=0; i<this.schema.devicetypes[deviceType].properties.length; i++ )
            {
                prop = this.schema.devicetypes[deviceType].properties[i];
                if( this.schema.values[prop]!==undefined )
                {
                    if( this.schema.values[prop].type!==undefined && this.schema.values[prop].name!==undefined )
                    {
                        var content = {};
                        content.id = prop;
                        for( var item in  this.schema.values[prop] )
                        {
                            if( item!==undefined )
                                content[item] = this.schema.values[prop][item];
                        }
                        props[this.schema.values[prop].name] = content;
                    }
                }
            }
        }
        return props;
    },

    //get device commands
    getDeviceCommands: function(deviceType) {
        var cmds = {};
        if( this.schema.devicetypes[deviceType]!==undefined && this.schema.devicetypes[deviceType].commands!==undefined )
        {
            var cmd;
            for( var i=0; i<this.schema.devicetypes[deviceType].commands.length; i++ )
            {
                cmd = this.schema.devicetypes[deviceType].commands[i];
                if( this.schema.commands[cmd]!==undefined )
                {
                    if( this.schema.commands[cmd].name!==undefined )
                    {
                        var content = {};
                        content.id = cmd;
                        for( var item in this.schema.commands[cmd] )
                        {
                            if( item!==undefined )
                                content[item] = this.schema.commands[cmd][item];
                        }
                        cmds[cmd] = content;
                    }
                }
            }
        }
        return cmds;
    },

    //get value
    getValue: function(valueName) {
        var output = {name:null, type:null, options:null};
        if( this.schema.values[valueName]!==undefined && this.schema.values[valueName].name!==undefined )
        {
            output.name = this.schema.values[valueName]['name'];
            if( this.schema.values[valueName].type!==undefined )
            {
                output.type = this.schema.values[valueName].type;
            }
            if( this.schema.values[valueName].options!==undefined )
            {
                output.options = this.schema.values[valueName].options;
            }
        }
        //console.log(output);
        return output;
    },
    
    //get variables
    getVariables: function() {
        var variables = [];
        for( var i=0; i<this.variables.length; i++ )
        {
            variables.push([this.variables[i], this.variables[i]]);
        }
        if( variables.length===0 )
        {
            variables.push(['', '']);
        }
        return variables;
    },
    
    //clear blockly container
    clearAllBlocks: function(container) {
        if( container===undefined )
            return;
        if( container.fieldRow===undefined )
            console.log('Warning: specified container is not an Input. Unable to clear blocks within.');
        //hack to remove all fields from container (code extracted from core/input.js)
        var field;
        for( var i=container.fieldRow.length-1; i>=0; i--)
        {
            field = container.fieldRow[i];
            field.dispose();
            container.fieldRow.splice(i, 1);
        }
        if (container.sourceBlock_.rendered)
        {
            container.sourceBlock_.render();
            // Removing a field will cause the block to change shape.
            container.sourceBlock_.bumpNeighbours_();
        }
    }
};

//====================================
//ADDITIONAL CORE FUNCTIONS
//====================================

Blockly.FieldTextInput.emailValidator = function(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email) ? email : null;
};

Blockly.FieldTextInput.phoneNumberValidator = function(phonenumber) {
    var re = /^[a-z]{2}\*[0-9\s]*$/i;
    if( re.test(phonenumber) )
    {
        var parts = phonenumber.split("*");
        var res = phoneNumberParser(parts[1], parts[0]);
        if( res["result"]===false )
            return null;
        else
            return res["phone"];
    }
    else
        return null;
};

//====================================
//AGOCONTROL BLOCKS
//====================================

goog.provide('Blockly.Blocks.agocontrol');
goog.require('Blockly.Blocks');

//no device
Blockly.Blocks['agocontrol_deviceNo'] = {
  init: function() {
    //this.setHelpUrl('TODO');
    this.setColour(20);
    this.appendDummyInput()
        .appendField("No device");
    this.setOutput(true, "Device");
    this.setTooltip('No device selected');
  }
};

//device block
Blockly.Blocks['agocontrol_device'] = {
  init: function() {
    //members
    this.lastType = undefined;

    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(20);
    this.container = this.appendDummyInput()
        //.appendField("device")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getDeviceTypes()), "TYPE")
        .appendField(new Blockly.FieldDropdown([['','']]), "DEVICE");
    this.setInputsInline(true);
    this.setOutput(true, "Device");
    this.setTooltip('Return device uuid');
  },

  onchange: function() {
    if( !this.workspace )
        return;
    var currentType = this.getFieldValue("TYPE");
    if( this.lastType!=currentType )
    {
        this.lastType = currentType;
        var devices = window.BlocklyAgocontrol.getDevices(currentType);
        if( devices.length===0 )
            devices.push(['','']);
        this.container.removeField("DEVICE");
        this.container.appendField(new Blockly.FieldDropdown(devices), "DEVICE");
    }
  }
};

//no event
Blockly.Blocks['agocontrol_eventNo'] = {
  init: function() {
    //this.setHelpUrl('TODO');
    this.setColour(65);
    this.appendDummyInput()
        .appendField("No event");
    this.setOutput(true, "Event");
    this.setTooltip('Return no event');
  }
};

//device event block
Blockly.Blocks['agocontrol_deviceEvent'] = {
  init: function() {
    //members
    this.lastType = undefined;
    this.lastDevice = undefined;
    
    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(65);
    this.container = this.appendDummyInput()
        //.appendField("event")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getDeviceTypes()), "TYPE")
        .appendField(new Blockly.FieldDropdown([['','']]), "DEVICE")
        .appendField("", "SEP")
        .appendField(new Blockly.FieldDropdown([['','']]), "EVENT");
    this.setInputsInline(true);
    this.setOutput(true, "Event");
    this.setTooltip('Return device event name');
  },

  onchange: function() {
    if( !this.workspace )
        return;
    var currentType = this.getFieldValue("TYPE");
    if( this.lastType!=currentType )
    {
        this.lastType = currentType;
        var devices = window.BlocklyAgocontrol.getDevices(currentType);
        if( devices.length===0 )
            devices.push(['','']);
        this.container.removeField("DEVICE");
        this.container.appendField(new Blockly.FieldDropdown(devices), "DEVICE");
    }
    var currentDevice = this.getFieldValue("DEVICE");
    if( this.lastDevice!=currentDevice )
    {
        this.lastDevice = currentDevice;
        var events = [];
        if( currentDevice.length>0 )
        {
            events = window.BlocklyAgocontrol.getDeviceEvents(currentType);
            if( events.length===0 )
                events.push(['','']);
        }
        else
        {
            events.push(['','']);
        }
        this.container.removeField("SEP");
        this.container.removeField("EVENT");
        this.container.appendField(" ", "SEP");
        this.container.appendField(new Blockly.FieldDropdown(events), "EVENT");
    }
  }
};

//all events block
Blockly.Blocks['agocontrol_eventAll'] = {
  init: function() {
    //this.setHelpUrl('TODO');
    this.setColour(65);
    this.container = this.appendDummyInput()
        //.appendField("event")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getAllEvents()), "EVENT");
    this.setInputsInline(true);
    this.setOutput(true, "Event");
    this.setTooltip('Return event name');
  }
};

//device property block
Blockly.Blocks['agocontrol_deviceProperty'] = {
  init: function() {
    //members
    this.properties = undefined;
    this.lastType = undefined;
    this.lastDevice = undefined;

    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(140);
    this.container = this.appendDummyInput()
        //.appendField("property")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getDeviceTypes()), "TYPE")
        .appendField(new Blockly.FieldDropdown([['','']]), "DEVICE")
        .appendField(" ", "SEP")
        .appendField(new Blockly.FieldDropdown([['','']]), "PROP");
    this.setInputsInline(true);
    this.setOutput(true, "DeviceProperty");
    this.setTooltip('Return device property name');
  },

  //onchange event
  onchange: function() {
    if( !this.workspace )
        return;

    //update properties list
    var currentType = this.getFieldValue("TYPE");
    if( this.lastType!=currentType )
    {
        this.lastType = currentType;
        var devices = window.BlocklyAgocontrol.getDevices(currentType);
        if( devices.length===0 )
            devices.push(['','']);
        this.container.removeField("DEVICE");
        this.container.appendField(new Blockly.FieldDropdown(devices), "DEVICE");
    }

    var currentDevice = this.getFieldValue("DEVICE");
    if( this.lastDevice!=currentDevice )
    {
        this.lastDevice = currentDevice;
        var props = [];
        if( currentDevice.length>0 )
        {
            this.properties = window.BlocklyAgocontrol.getDeviceProperties(currentType);
            for( var prop in this.properties )
            {
                props.push([prop, this.properties[prop].name]);
            }
            if( props.length===0 )
                props.push(['','']);
        }
        else
        {
            props.push(['','']);
        }
        this.container.removeField("SEP");
        this.container.removeField("PROP");
        this.container.appendField(" ", "SEP");
        this.container.appendField(new Blockly.FieldDropdown(props), "PROP");
    }
  }
};

//event property block
Blockly.Blocks['agocontrol_eventProperty'] = {
  init: function() {
    //members
    this.properties = undefined;
    this.lastEvent = undefined;

    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(140);
    this.container = this.appendDummyInput()
        //.appendField("property")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getAllEvents()), "EVENT")
        .appendField(new Blockly.FieldDropdown([['','']]), "PROP");
    this.setInputsInline(true);
    this.setOutput(true, "EventProperty");
    this.setTooltip('Return event property name');
  },

  //onchange event
  onchange: function() {
    if( !this.workspace )
        return;

    //update properties list
    var currentEvent = this.getFieldValue("EVENT");
    if( this.lastEvent!=currentEvent )
    {
        this.lastEvent = currentEvent;
        var events = window.BlocklyAgocontrol.getEventProperties(currentEvent);
        if( events.length===0 )
            events.push(['','']);
        this.container.removeField("PROP");
        this.container.appendField(new Blockly.FieldDropdown(events), "PROP");
        var myparent = this.getParent();
        if( myparent && myparent.type && myparent.type==="agocontrol_eventPropertyValue")
        {
            myparent.onchange();
        }
    }
  }
};

//event property values
Blockly.Blocks['agocontrol_eventPropertyValue'] = {
  init: function() {
    //members
    this.customFields = [];
    this.currentType = null;
    this.lastProp = null;

    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(210);
    this.container = this.appendValueInput("PROP")
        //.appendField("property")
        .setCheck(["EventProperty", "DeviceProperty"]);
    this.ccontainer = this.appendDummyInput();
    this._addCustomField("empty", new Blockly.FieldImage("/blockly/media/1x1.gif",1,1,""));
    this.setInputsInline(true);
    this.setOutput(true, "Boolean");
    this.setTooltip('Return true if property is equal to value');
    
    //add default fields
    this._defaultFields();
  },
  
  //generate output xml according to block content
  mutationToDom: function() {
    var container = document.createElement('mutation');
    container.setAttribute('currentprop', this.lastProp);
    container.setAttribute('currenttype', this.currentType);
    return container;
  },
  
  //generate block content according to input xml
  domToMutation: function(xmlElement) {
    var currentProp = xmlElement.getAttribute('currentprop');
    this.currentType = xmlElement.getAttribute('currenttype');
    this._generateContent(currentProp);
  },

  //get block values
  getValues: function() {
    var values = {};
    for( var i=0; i<this.customFields.length; i++)
    {
      if( this.customFields[i]!='empty' && this.customFields[i]!='text' )
      {
        values[this.customFields[i]] = this.getFieldValue("CUSTOM_"+this.customFields[i]);
      }
    }
    return values;
  },

  //add custom field (internal use)
  _addCustomField: function(key, field) {
    this.customFields.push(key);
    this.ccontainer.appendField(field, "CUSTOM_"+key);
  },

  //clear custom fields (internal use);
  _clearCustomFields: function() {
    for( var i=0; i<this.customFields.length; i++)
    {
      this.ccontainer.removeField("CUSTOM_"+this.customFields[i]);
    }
    while( this.customFields.length>0 )
    {
      this.customFields.pop();
    }
  },
  
  //add default fields
  _defaultFields: function() {
    this._addCustomField("SIGN", new Blockly.FieldDropdown([["=","eq"],["!=","di"],[">","gt"],["<","lt"],[">=","gte"],["<=","lte"]]));
    this._addCustomField("VALUE", new Blockly.FieldTextInput("0"));
  },
  
  //generate block content
  _generateContent: function(currentProp) {
    if( this.lastProp!=currentProp )
    {
        this._clearCustomFields();
        var value = window.BlocklyAgocontrol.getValue(currentProp);
        this.currentType = value.type;
        this.lastProp = currentProp;
        switch(value.type)
        {
            case 'option':
                var opts = [];
                for( var i=0; i<value.options.length; i++ )
                {
                    opts.push([value.options[i], value.options[i]]);
                }
                this._addCustomField("text", "=");
                this._addCustomField("OPTION", new Blockly.FieldDropdown(opts));
                break;
            case 'range':
                this._addCustomField("text", "in range [");
                this._addCustomField("MIN", new Blockly.FieldTextInput("0"));
                this._addCustomField("text", ",");
                this._addCustomField("MAX", new Blockly.FieldTextInput("100"));
                this._addCustomField("text", "]");
                break;
            case 'color':
                this._addCustomField("text", "has colour");
                this._addCustomField("COLOR", new Blockly.FieldColour("#000000"));
                break;
            case 'time':
                this._addCustomField("text", "is");
                this._addCustomField("HOUR", new Blockly.FieldTextInput("0"));
                this._addCustomField("text", ":");
                this._addCustomField("MINUTE", new Blockly.FieldTextInput("0"));
                break;
            case 'timeoffset':
                this._addCustomField("text", "has offset");
                this._addCustomField("SIGN", new Blockly.FieldDropdown([["-","minus"],["+","plus"]]));
                this._addCustomField("HOUR", new Blockly.FieldTextInput("0"));
                this._addCustomField("text", ":");
                this._addCustomField("MINUTE", new Blockly.FieldTextInput("0"));
                break;
            case 'threshold':
                this._addCustomField("text", "is");
                this._addCustomField("SIGN", new Blockly.FieldDropdown([[">","gt"],["<","lt"],[">=","gte"],["<=","lte"]]));
                this._addCustomField("THRESHOLD", new Blockly.FieldTextInput("0"));
                break;
            case 'bool':
                this._addCustomField("text", "is");
                this._addCustomField("BOOL", new Blockly.FieldDropdown([["true","true"],["false","false"]]));
                break;
            case 'email':
                this._addCustomField("text", "is");
                this._addCustomField("EMAIL", new Blockly.FieldTextInput('john@smith.com', Blockly.FieldTextInput.emailValidator));
                break;
            case 'colour':
                this._addCustomField("text", "is");
                this._addCustomField("COLOUR", new Blockly.FieldColour('#ff0000'));
                break;
            case 'phone':
                this._addCustomField("text", "is");
                this._addCustomField("PHONE", new Blockly.FieldTextInput('us*562 555 5555', Blockly.FieldTextInput.phoneNumberValidator));
                break;
            default:
                //not defined value, display standard field
                this._defaultFields();
                break;
        }
    }
  },

  //onchange
  onchange: function() {
    if( !this.workspace )
        return;
    if( this.getChildren().length===0 )
        return;

    //update block content according to selected type
    var child = this.getChildren()[0];
    var currentProp = child.getFieldValue("PROP");
    this._generateContent(currentProp);
  }
};

//device command
Blockly.Blocks['agocontrol_sendMessage'] = {
  init: function() {
    //members
    this.commands = undefined;
    this.lastType = undefined;
    this.lastDevice = undefined;
    this.lastCommand = undefined;
    this.customFields = [];
    this.customBlocks = [];

    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(290);
    this.appendDummyInput()
        .appendField("sendMessage");
    this.container = this.appendDummyInput()
        .appendField("to device")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getDeviceTypes()), "TYPE")
        .appendField(new Blockly.FieldDropdown([['','']]), "DEVICE");
    this.containerCommand = this.appendDummyInput()
        .appendField("command")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField(new Blockly.FieldDropdown([['','']]), "COMMAND");
    //this.setOutput(true, "Command");
    this.setPreviousStatement(true, "null");
    this.setNextStatement(true, "null");
    //this.setTooltip('Return device command name');
    this.setTooltip('Send a message to execute a command on agocontrol');
  },
  
  //generate output xml according to block content
  mutationToDom: function() {
    var container = document.createElement('mutation');
    container.setAttribute('currenttype', this.lastType);
    container.setAttribute('currentdevice', this.lastDevice);
    container.setAttribute('currentcommand', this.lastCommand);
    container.setAttribute('duplicated', ((this.customBlocks.length===0) ? false : true));
    return container;
  },
  
  //generate block content according to input xml
  domToMutation: function(xmlElement) {
    var currentType = xmlElement.getAttribute('currenttype');
    var currentDevice = xmlElement.getAttribute('currentdevice');
    var currentCommand = xmlElement.getAttribute('currentcommand');
    var duplicated = xmlElement.getAttribute('duplicated');
    this._generateContent(currentType, currentDevice, currentCommand, duplicated);
  },
  
  //get fields name
  getFields: function() {
    var fields = {};
    for( var i=0; i<this.customFields.length; i++)
    {
        if( this.customFields[i]!='empty' && this.customFields[i]!='text' )
        {
            fields["CUSTOM_"+this.customFields[i]] = this.customFields[i];
        }
    }
    return fields;
  },

  //add custom field (internal use)
  _addCustomField: function(key, desc, checkType, extra, duplicated) {
    //create new input
    var workspace = Blockly.getMainWorkspace();
    var newBlock;
    //duplicate operation creates dependant blocks by itself, so no need to create them twice
    if( !duplicated )
    {
        switch( checkType )
        {
            case "Number":
                newBlock = Blockly.Block.obtain(workspace, 'math_number');
                break;
            case "Boolean":
                newBlock = Blockly.Block.obtain(workspace, 'logic_boolean'); 
                break;
            case "String":
                newBlock = Blockly.Block.obtain(workspace, 'text');
                break;
            case "Option":
                checkType = "String"; //force check type to Blockly known type
                newBlock = Blockly.Block.obtain(workspace, 'agocontrol_fixedItemsList');
                newBlock.setItems(extra);
                break;
            case "Email":
                newBlock = Blockly.Block.obtain(workspace, 'agocontrol_email');
                break;
            case "Colour":
                newBlock = Blockly.Block.obtain(workspace, 'colour_picker');
                break;
            case "Phone":
                newBlock = Blockly.Block.obtain(workspace, 'agocontrol_phoneNumber');
                break;
            default:
                newBlock = Blockly.Block.obtain(workspace, 'text');
                break;
        }
        newBlock.initSvg();
    }

    //create custom field
    var input = this.appendValueInput("CUSTOM_"+key)
                .setAlign(Blockly.ALIGN_RIGHT)
                .setCheck(checkType);
    this.customFields.push(key);
    if( desc!==undefined && desc.length>0 )
    {
        input.appendField('- '+desc);
    }
    else
    {
        //no description in schema.yaml, use name instead
        input.appendField('- '+key);
    }
    if( !duplicated )
    {
        newBlock.outputConnection.connect(input.connection);
        newBlock.render();
        this.customBlocks.push(newBlock);
    }
  },

  //clear custom fields (internal use);
  _clearCustomFields: function() {
    for( var i=0; i<this.customFields.length; i++)
    {
        //get input
        var input = this.getInput("CUSTOM_"+this.customFields[i]);
        if( input!==undefined )
        {
            if( input.connection!==null )
            {
                input.connection.targetConnection.sourceBlock_.dispose();
            }
            this.removeInput("CUSTOM_"+this.customFields[i]);
        }
    }
    while( this.customFields.length>0 )
    {
        this.customFields.pop();
    }
    while( this.customBlocks.length>0 )
    {
        var block = this.customBlocks.pop();
        block.dispose();
    }
  },
  
  //generate content
  _generateContent: function(currentType, currentDevice, currentCommand, duplicated) {
    //update devices list
    if( !currentType )
        currentType = this.getFieldValue("TYPE");
    if( this.lastType!=currentType )
    {
        this.lastType = currentType;
        var devices = window.BlocklyAgocontrol.getDevices(currentType);
        if( devices.length===0 )
            devices.push(['','']);
        this.container.removeField("DEVICE");
        this.container.appendField(new Blockly.FieldDropdown(devices), "DEVICE");
    }
    
    //update commands list
    if( !currentDevice )
        currentDevice = this.getFieldValue("DEVICE");
    if( this.lastDevice!=currentDevice )
    {
        this.lastDevice = currentDevice;
        var cmds = [];
        if( currentDevice.length>0 )
        {
            this.commands = window.BlocklyAgocontrol.getDeviceCommands(currentType);
            for( var cmd in this.commands )
            {
                cmds.push([this.commands[cmd].name, this.commands[cmd].id]);
            }
            if( cmds.length===0 )
                cmds.push(['','']);
        }
        else
        {
            cmds.push(['','']);
        }
        window.BlocklyAgocontrol.clearAllBlocks(this.containerCommand);
        this.containerCommand.appendField("command");
        this.containerCommand.appendField(new Blockly.FieldDropdown(cmds), "COMMAND");
    }

    //update block content according to selected type
    if( !currentCommand )
        currentCommand = this.getFieldValue("COMMAND");
    if( this.lastCommand!=currentCommand )
    {
        this.lastCommand = currentCommand;
        this._clearCustomFields();
        if( currentCommand.length>0 && this.commands[currentCommand]!==undefined && this.commands[currentCommand].parameters!==undefined )
        {
            for( var param in this.commands[currentCommand].parameters )
            {
                var type = "null"; //default is any type (no type check)
                var extra = null;
                if( this.commands[currentCommand].parameters[param].type!==undefined )
                {
                    switch( this.commands[currentCommand].parameters[param].type )
                    {
                        case "integer":
                            type = "Number";
                            break;
                        case "string":
                            type = "String";
                            break;
                        case "number":
                            type = "Number";
                            break;
                        case "boolean":
                            type = "Boolean";
                            break;
                        case "option":
                            //"Option" type is not a Blockly recognized type
                            type = "Option";
                            if( this.commands[currentCommand].parameters[param].options!==undefined )
                            {
                                extra = [];
                                for( var i=0; i<this.commands[currentCommand].parameters[param].options.length; i++)
                                {
                                    extra.push([this.commands[currentCommand].parameters[param].options[i], this.commands[currentCommand].parameters[param].options[i]]);
                                }
                            }
                            break;
                        case "email":
                            type = "Email";
                            break;
                        case "colour":
                            type = "Colour";
                            break;
                        case "phone":
                            type = "Phone";
                            break;
                        default:
                            //allow any type
                            type = null;
                            break;
                    }
                }
                this._addCustomField(param, this.commands[currentCommand].parameters[param].name, type, extra, duplicated);
            }
        }
    }
  },

  //onchange event
  onchange: function() {
    if( !this.workspace )
        return;

    //update commands list
    this._generateContent(null, null, null, false);
  }
};

/*DEPRECATED. CODE STAYS HERE FOR FURTHER USE
//sendMessage block
Blockly.Blocks['agocontrol_sendMessage'] = {
  init: function() {
    //this.setHelpUrl('TODO');
    this.setColour(290);
    this.appendDummyInput()
        .appendField("sendMessage");
    this.appendValueInput("COMMAND")
        .setCheck("Command")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("command");
    this.setPreviousStatement(true, "null");
    this.setNextStatement(true, "null");
    this.setTooltip('Send a message to execute a command on agocontrol');
  }
};*/

//content condition
Blockly.Blocks['agocontrol_contentCondition'] = {
    init: function() {
        //this.setHelpUrl('TODO');
        this.setColour(210);
        this.appendDummyInput()
            .appendField("triggered event is");
        this.appendValueInput("EVENT")
            .setCheck("Event");
        this.setInputsInline(true);
        this.setOutput(true, "Boolean");
        this.setTooltip('Return true if event is triggered one');
    }
};

//get variable block
Blockly.Blocks['agocontrol_getVariable'] = {
    init: function() {
        //block definition
        //this.setHelpUrl('TODO');
        this.setColour(330);
        this.appendDummyInput()
            .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getVariables()), "VARIABLE");
        this.setOutput(true, "String");
        this.setTooltip('Return the value of selected agocontrol variable');
    },
    
    //return selected variable name
    getVariable: function() {
        return this.getFieldValue("VARIABLE") || '';
    }
};

//set variable block
Blockly.Blocks['agocontrol_setVariable'] = {
  init: function() {
    //block definition
    //this.setHelpUrl('TODO');
    this.setColour(330);
    this.appendValueInput("VALUE")
        .setCheck(null)
        .appendField("set")
        .appendField(new Blockly.FieldDropdown(window.BlocklyAgocontrol.getVariables()), "VARIABLE")
        .appendField("to");
    this.setInputsInline(true);
    this.setPreviousStatement(true, "null");
    this.setNextStatement(true, "null");
    this.setTooltip('Set this agocontrol variable to be equal to the input');
  },
    
    //return selected variable name
    getVariable: function() {
        return this.getFieldValue("VARIABLE") || '';
    }
};

//list of fixed items
Blockly.Blocks['agocontrol_fixedItemsList'] = {
  init: function() {
    //members
    this.items = [['','']]; //empty list
    
    //block definition
    //this.setHelpUrl("TODO");
    this.setColour(160);
    this.setOutput(true, 'String');
    this.container = this.appendDummyInput()
        .appendField(new Blockly.FieldDropdown(this.items), 'LIST');
    this.setTooltip("Return the selected list item");
  },
  
  //set list items
  //items must be list [['key','val'], ...]
  setItems: function(items) {
    //regenerate list
    this.container.removeField("LIST");
    //prevent from js crash
    if( items.length===0 )
        items = [['','']];
    this.container.appendField(new Blockly.FieldDropdown(items), "LIST");
  },
  
  //return selected item
  getSelectedItem: function() {
    return this.getFieldValue("LIST") || '';
  }
};

//email block
Blockly.Blocks['agocontrol_email'] = {
  init: function() {
    //this.setHelpUrl('TODO');
    this.setColour(160);
    this.appendDummyInput()
        .appendField(new Blockly.FieldTextInput('john@smith.com', Blockly.FieldTextInput.emailValidator), 'EMAIL');
    this.setOutput(true, 'Email');
    this.setTooltip("An email");
  }
};

//phone number block
Blockly.Blocks['agocontrol_phoneNumber'] = {
  init: function() {
    this.setHelpUrl('http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements');
    this.setColour(160);
    this.appendDummyInput()
        .appendField(new Blockly.FieldTextInput('us*562 555 5555', Blockly.FieldTextInput.phoneNumberValidator), 'PHONE');
    this.setOutput(true, 'Phone');
    this.setTooltip("A phone number <Alpha-2 code>*<real phone number>");
  }
};

//sleep function
Blockly.Blocks['agocontrol_sleep'] = {
  init: function() {
    //this.setHelpUrl('TODO');
    this.setColour(290);
    this.appendValueInput("DURATION")
        .setCheck("Number")
        .appendField("sleep during");
    this.appendDummyInput()
        .appendField("seconds");
    this.setInputsInline(true);
    this.setPreviousStatement(true, "null");
    this.setNextStatement(true, "null");
    this.setTooltip('Sleep during specified amount of seconds (be carefull it will defer other script!)');
  }
};

