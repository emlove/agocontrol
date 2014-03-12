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
                //path: "blockly/",
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
