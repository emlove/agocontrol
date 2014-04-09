'use strict';

goog.provide('Blockly.Lua.agocontrol');

goog.require('Blockly.Lua');

Blockly.Lua['agocontrol_deviceNo'] = function(block) {
    return ["''", Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_device'] = function(block) {
    var code = "'" + block.getFieldValue('DEVICE') + "'";
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_eventNo'] = function(block) {
    return ["''", Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_deviceEvent'] = function(block) {
    var code = block.getFieldValue('EVENT');
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_eventAll'] = function(block) {
    var code = block.getFieldValue('EVENT');
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_deviceProperty'] = function(block) {
    var code = "";
    if( block.inContent )
        code = "content." + block.getFieldValue("PROP");
    else
        code = block.getFieldValue("PROP");
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_eventProperty'] = function(block) {
    var code = "";
    if( block.inContent )
        code = "content." + block.getFieldValue("PROP");
    else
        code = block.getFieldValue("PROP");
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_sendMessage'] = function(block) {
    var code = "";
    var value;
    var command = block.getFieldValue("COMMAND") || 'nil';
    var device = block.getFieldValue("DEVICE") || 'nil';
    var fields = block.getFields();
    code += "'command="+command+"', 'uuid="+device+"' ";
    for( var field in fields )
    {
        value = Blockly.Lua.valueToCode(block, field, Blockly.Lua.ORDER_NONE) || '';
        //always concat value to field name because of computed value (like string concat, operation...)
        code += ", '"+fields[field]+"=' .. "+value;
    }
    return "sendMessage("+code+")\n";
};

Blockly.Lua['agocontrol_content'] = function(block) {
    var code = "";
    code += "content.subject == \"";
    code += Blockly.Lua.valueToCode(block, 'EVENT', Blockly.Lua.ORDER_NONE) || 'nil';
    code += "\"";
    for( var i=1; i<=block._conditionCount; i++ )
    {
        if( block.getFieldValue('COND'+i)=="OR" )
            code += " or ";
        else
            code += " and ";
        code += Blockly.Lua.valueToCode(block, 'PROP'+i, Blockly.Lua.ORDER_NONE) || '';
    }
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_fixedItemsList'] = function(block) {
    var code = "'"+block.getSelectedItem()+"'";
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_email'] = function(block) {
  var code = Blockly.Lua.quote_(block.getFieldValue('EMAIL'));
  return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_phoneNumber'] = function(block) {
  var code = Blockly.Lua.quote_(block.getFieldValue('PHONE'));
  return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_getVariable'] = function(block) {
    var code = "inventory.variables."+block.getVariable();
    return [code, Blockly.Lua.ORDER_NONE];
};

Blockly.Lua['agocontrol_setVariable'] = function(block) {
    var code = "";
    var name = block.getVariable();
    if( name.length>0 )
    {
        code = "setVariable('"+name+"=";
        code += Blockly.Lua.valueToCode(block, 'VALUE', Blockly.Lua.ORDER_NONE) || 'nil';
        code += "')\n";
        return code;
    }
    return '';
};

Blockly.Lua['agocontrol_sleep'] = function(block) {
    var code = "";
    var dur = Blockly.Lua.valueToCode(block, 'DURATION', Blockly.Lua.ORDER_NONE) || 1;
    code = "local time_to = os.time() + "+dur+"\n";
    code += "while os.time() < time_to do end\n";
    return code;
};

Blockly.Lua['agocontrol_range'] = function(block) {
    var code = "(";
    var prop = Blockly.Lua.valueToCode(block, 'PROP', Blockly.Lua.ORDER_NONE) || '';
    code += prop;
    if( block.getFieldValue('SIGN_MIN')=="LT" )
        code += " > ";
    else
        code += " >= ";
    code += Blockly.Lua.valueToCode(block, 'MIN', Blockly.Lua.ORDER_NONE) || 1;
    code += " and ";
    code += prop;
    if( block.getFieldValue('SIGN_MAX')=="LT" )
        code += " < ";
    else
        code += " <= ";
    code += Blockly.Lua.valueToCode(block, 'MAX', Blockly.Lua.ORDER_NONE) || 100;
    code += ")";
    return [code, Blockly.Lua.ORDER_ATOMIC];
};

Blockly.Lua['agocontrol_valueOptions'] = function(block) {
    var code = "'"+block.getSelectedOption()+"'";
    return [code, Blockly.Lua.ORDER_ATOMIC];
};
