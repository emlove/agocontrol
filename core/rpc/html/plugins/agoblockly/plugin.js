/**
 * Agoblockly plugin
 * @returns {agoblockly}
 */
function agoBlocklyPlugin(deviceMap) {
    //members
    var self = this;
    this.hasNavigation = ko.observable(false);
    /*this.eventControllerUuid;

    //fill available scenarios and get agoscheduler uuid
    if( deviceMap!==undefined )
    {
            if( deviceMap[i].devicetype=='eventcontroller' )
            {
                self.eventControllerUuid = deviceMap[i].uuid;
                break;
            }
        }
    }*/

    //get unconnected block
    self.getUnconnectedBlock = function() {
        var blocks = Blockly.mainWorkspace.getAllBlocks();
        for (var i = 0, block; block = blocks[i]; i++)
        {
            var connections = block.getConnections_(true);
            for (var j = 0, conn; conn = connections[j]; j++)
            {
                if (!conn.sourceBlock_ || (conn.type == Blockly.INPUT_VALUE || conn.type == Blockly.OUTPUT_VALUE) && !conn.targetConnection)
                {
                    return block;
                }
            }
        }
        return null;
    };
    
    //get block with warning
    self.getBlockWithWarning = function()
    {
        var blocks = Blockly.mainWorkspace.getAllBlocks();
        for (var i = 0, block; block = blocks[i]; i++)
        {
            if (block.warning)
            {
                return block;
            }
        }
        return null;
    };
    
    //blink specified block
    self.blinkBlock = function(block)
    {
        for(var i=300; i<3000; i=i+300)
        {
            setTimeout(function() { block.select(); },i);
            setTimeout(function() { block.unselect(); },i+150);
        }
    };

    //check blocks
    self.checkBlocks = function(notifySuccess) {
        var warningText;
        var badBlock = self.getUnconnectedBlock();
        if (badBlock)
        {
            warningText = 'This block is not properly connected to other blocks.';
        }
        else
        {
            badBlock = self.getBlockWithWarning();
            if (badBlock)
            {
                warningText = 'Please fix the warning on this block.';
            }
        }

        if (badBlock)
        {
            notif.error(warningText);
            self.blinkBlock(badBlock);
            return false;
        }

        if( notifySuccess )
            notif.success('All blocks seems to be valid');

        return true;
    };

    //============================
    //button events
    //============================

    //clear everything
    self.clear = function() {
        var count = Blockly.mainWorkspace.getAllBlocks().length;
        if( count<2 || window.confirm("Delete everything?") )
        {
            Blockly.mainWorkspace.clear();
            //TODO window.location.hash = '';
        }
    };

    //check
    self.check = function() {
        self.checkBlocks(true);
    };

    //save code
    self.save = function() {
        notif.info('TODO');
    };

    //load code
    self.load = function() {
        notif.info('TODO');
    };

    //view lua source code
    self.viewlua = function() {
        //check code first
        if( !self.checkBlocks(false) )
            return;

        //fill dialog content
        var content = document.getElementById('luaContent');
        var code = Blockly.Lua.workspaceToCode();
        content.textContent = code;
        if (typeof prettyPrintOne == 'function')
        {
            code = content.innerHTML;
            code = prettyPrintOne(code, 'lang-lua');
            content.innerHTML = code;
        }
        //open dialog
        $( "#luaDialog" ).dialog({
            modal: true,
            title: "LUA script",
            height: 600,
            width: 1024
        });
    };

    //init blockly
    self.initBlockly = function(elements) {
        console.log('init blockly');
        console.log($('#blocklyDiv'));
        console.log(document);
        Blockly.inject( $('#blocklyDiv'), {path: './plugins/agoblockly/blockly/', toolbox: document.getElementById('toolbox')});
        if( BlocklyAgocontrol.init!==undefined )
            BlocklyAgocontrol.init(schema, deviceMap);
        else
            notif.error('Unable to initialize agoblockly', 0);
            console.log('Agocontrol is undefined!. Blockly not configured');
    };

    this.blocklyViewModel = new ko.blockly.viewModel({ });
}

/**
 * Entry point: mandatory!
 */
function init_plugin()
{
    ko.blockly = {
        viewModel: function(config) { }
    };

    ko.bindingHandlers.blockly = {
        update: function(element, viewmodel) {
            element.innerHTML = "";
            //inject blockly
            Blockly.inject( document.getElementById('blocklyDiv'), {
                path: "/plugins/agoblockly/blockly/",
                toolbox: document.getElementById('toolbox')
            });
            //init agoblockly
            if( BlocklyAgocontrol!=null && BlocklyAgocontrol.init!==undefined )
                BlocklyAgocontrol.init(schema, deviceMap);
            else
                notif.error('Unable to configure Blockly! Event builder shouldn\'t work.');
        }
    };

    model = new agoBlocklyPlugin(deviceMap);
    model.mainTemplate = function() {
        return templatePath + "agoblockly";
    }.bind(model);
    ko.applyBindings(model);
}
