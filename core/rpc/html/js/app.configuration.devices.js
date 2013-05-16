/* This is an app in the app  of the MVC model */
App.TableConfigurationDevices = Ember.Namespace.create();
App.TableConfigurationDevices = Ember.Table.TableController.extend({
    hasHeader: true,
    hasFooter: false,
    numFixedColumns: 0,
    numRows: 500000,
    rowHeight: 30,
    columns: Ember.computed(function() {
      var columnNames, columns, dateColumn, entryColumn;
      columnNames = ['name', 'devicetype', 'handled-by', 'internalid', 'room'];
      entryColumn = Ember.Table.ColumnDefinition.create({
        columnWidth: 100,
        headerCellName: 'Entry',
        getCellContent: function(row) {
          return deviceMap['uuid'];
        }
      });
      columns = columnNames.map(function(key, index) {
        var name;
        name = key.charAt(0).toUpperCase() + key.slice(1);
        return Ember.Table.ColumnDefinition.create({
          columnWidth: 100,
          headerCellName: name,
          getCellContent: function(row) {
            return deviceMap[key].toFixed(2);
          }
        });
      });
      columns.unshift(entryColumn);
      return columns;
    }).property(),
});

/* Maintains data gets events from the outside */
App.ConfigurationDevicesController = Ember.ObjectController.extend({
    content : [],

    updateDeviceMap : function() {
	var devs = [];
	for ( var k in deviceMap) {
	    if (deviceMap[k].devicetype == "scenario" || deviceMap[k].devicetype == "event" || deviceMap[k].devicetype == "zwavecontroller") {
		continue;
	    }
	    devs.push(deviceMap[k]);
	}
	this.set("content", devs);
    },

    tableConfigurationDevicesController: Ember.computed(function() {
      return Ember.get('App.TableConfigurationDevices').create();
    }).property(),


});

/* View */
App.ConfigurationDevicesView = Ember.View.extend({
    templateName : "configurationdevices",
    name : "ConfigurationDevices"
});

/* Route - glues view and controller */
App.ConfigurationDevicesRoute = Ember.Route.extend({
    model : function() {
	return [];
    },

    setupController : function(controller, model) {
	controller.set('content', model);
	activeController = controller;
	if (schema != {}) {
	    controller.updateDeviceMap();
	}
    },

    renderTemplate : function() {
	Ember.TEMPLATES['configurationdevices'] = App.getTemplate("configuration/devices");
	Ember.TEMPLATES['navigation_configuration'] = App.getTemplate("navigation/configuration");
	this.render('navigation_configuration', {
	    outlet : 'navigation'
	});
	this.render();
    }
});


Ember.Handlebars.registerBoundHelper('enableDSTableSorter', function(value, options) {
    Ember.run.next(function() {
	$("#donfigurationdevice").tablesorter(); 
    });
});

