'use strict';

goog.provide('Blockly.Lua.agocontrol');

goog.require('Blockly.Lua');

Blockly.Lua['agocontrol_deviceNo'] = function(block) {
    return ['', Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_device'] = function(block) {
    var code = block.getFieldValue('DEVICE');
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_eventNo'] = function(block) {
    return ['', Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_deviceEvent'] = function(block) {
    var code = block.getFieldValue('EVENT');
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_eventAll'] = function(block) {
    var code = block.getFieldValue('EVENT');
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_deviceProperty'] = function(block) {
    var code = block.getFieldValue("PROP");
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_eventProperty'] = function(block) {
    var code = block.getFieldValue("PROP");
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_eventPropertyValue'] = function(block) {
    var code = "";
    var values = block.getValues();
    var type = block.currentType;
    var prop = block.lastProp;
    code += "content."+prop+" ";
        switch(type)
        {
            case 'option':
                //OPTION
                code += "== '"+values["OPTION"]+"' ";
                break;
            case 'range':
                //MIN MAX
                code += ">= "+values["MIN"]+" and content."+prop+" <= "+values["MAX"];
                break;
            case 'color':
                //COLOR
                code += "== '"+values["COLOR"]+"'";
                break;
            case 'time':
                //HOUR MINUTE
                //TODO need to specify time format
                break;
            case 'timeoffset':
                //SIGN HOUR MINUTE
                //TODO need to specify time format
                break;
            case 'threshold':
                //SIGN THRESHOLD
                switch(values["SIGN"])
                {
                    case "gt": code += "> "; break;
                    case "lt": code += "< "; break;
                    case "ge": code += ">= "; break;
                    case "le": code += "<= "; break;
                }
                code += values["VALUE"]+" ";
                break;
            case 'bool':
                //BOOL
                code += "== "+values["BOOL"];
                break;
            default:
                //SIGN VALUE
                switch(values["SIGN"])
                {
                    case "eq": code += "== "; break;
                    case "di": code += "!= "; break;
                    case "gt": code += "> "; break;
                    case "lt": code += "< "; break;
                    case "ge": code += ">= "; break;
                    case "le": code += "<= "; break;
                }
                code += values["VALUE"]+" ";
                break;
        }
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_deviceCommand'] = function(block) {
    var code = "";
    var value;
    var cmd = block.getFieldValue("CMD") || 'nil';
    var fields = block.getFields();
    code += "'command="+cmd+"' ";
    for( var field in fields )
    {
        value = Blockly.Lua.valueToCode(block, field, Blockly.Lua.ORDER_NONE) || '';
        //remove single quotes if string
        if( value[0]=="'" && value[value.length-1]=="'" )
            value = value.substring(1,value.length-1);
        code += ", '"+fields[field]+"="+value+"'";
    }
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_sendMessage'] = function(block) {
    var code = "";
    code += Blockly.Lua.valueToCode(block, 'COMMAND', Blockly.Lua.ORDER_NONE) || 'nil';
    var device = Blockly.Lua.valueToCode(block, 'DEVICE', Blockly.Lua.ORDER_NONE) || null;
    if( device )
    {
        code += ", 'uuid="+device+"'";
    }
    return "sendMessage("+code+")\n";
};

Blockly.Lua['agocontrol_contentCondition'] = function(block) {
    var code = "";
    code += "content.subject == \"";
    code += Blockly.Lua.valueToCode(block, 'EVENT', Blockly.Lua.ORDER_NONE) || 'nil';
    code += "\"";
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_fixedItemsList'] = function(block) {
    var code = "'"+block.getSelectedItem()+"'";
    return [code, Blockly.Lua.ORDER_NONE];
};
