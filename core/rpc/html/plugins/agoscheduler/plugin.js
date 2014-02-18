/**
 * Agoscheduler plugin
 * @returns {agoscheduler}
 */
function agoSchedulerPlugin(deviceMap) {
    //members
    var self = this;
    this.viewDate = ko.observable(new Date());
    this.hasNavigation = ko.observable(false);
    this.schedules = ko.observableArray([]);
    this.availableStartScenarios = ko.observableArray([]);
    this.availableEndScenarios = ko.observableArray([]);
    this.selectedStartScenario = ko.observable('');
    this.selectedEndScenario = ko.observable('');
    this.scheduleStart = ko.observable();
    this.scheduleEnd = ko.observable();
    this.selectedRepeat = ko.observable('never');
    this.selectedColor = ko.observable('#C8C8C8');
    this.enableRepeat = ko.observable(false);
    this.agoschedulerUuid;

    //fill available scenarios and get agoscheduler uuid
    if( deviceMap!==undefined )
    {
        self.availableEndScenarios.push(new Option('None', '0', false, true));
        for( var i=0; i<deviceMap.length; i++ )
        {
            var first = true;
            if( deviceMap[i].devicetype=='scenario' )
            {
                var opt = new Option(deviceMap[i].name, deviceMap[i].uuid, false, first);
                if( first )
                    first = false;
                self.availableStartScenarios.push(opt);

                opt = new Option(deviceMap[i].name, deviceMap[i].uuid, false, false);
                self.availableEndScenarios.push(opt);
            }

            if( deviceMap[i].devicetype=='agoscheduler' )
            {
                self.agoschedulerUuid = deviceMap[i].uuid;
            }
        }
    }

    //get schedules
    this.getSchedules = function() {
        var content = {
            uuid: self.agoschedulerUuid,
            command: 'getSchedules'
        };
        sendCommand(content, function(res) {
            if( res!==undefined && res.result.result!==undefined )
            {
                for( var i=0; i<res.result.result.schedules.length; i++)
                {
                    //returned schedules are in fullCalendar format
                    self.schedules.push(res.result.result.schedules[i]);
                }
                //console.log(''+self.schedules().length+' loaded');
            }
            else
            {
                //TODO show error to user
                console.log('unable to get schedules list');
            }
        });
    };

    //add new schedule
    //recurring schedules are computed server-side
    this.addSchedule = function(sched) {
        //console.log('schedules len before add '+self.schedules().length);
        if( sched.scenarioStart!==undefined && sched.scenarioEnd!==undefined )
        {
            var content = {
                uuid: self.agoschedulerUuid,
                command: "addSchedule",
                title: sched.scenarioStart.text + '-' + sched.scenarioEnd.text,
                uuidStart: sched.scenarioStart.value,
                uuidEnd: sched.scenarioEnd.value,
                dateStart: moment(sched.start).format(),
                dateEnd: moment(sched.end).format(),
                color: sched.color,
                repeat: sched.repeat
            };

            //send new schedule to controller
            sendCommand(content, function(res) {
                if( res!==undefined && res.result.result!==undefined && res.result.result.error==0 )
                {
                    //and add all new schedules to fullCalendar
                    var item;
                    console.log('add '+res.result.result.schedules.length+' schedules');
                    for( var i=0; i<res.result.result.schedules.length; i++)
                    {
                        //returned schedules are in fullCalendar format
                        var pos = self.schedules.push(res.result.result.schedules[i]);
                        $('#schedulerCalendar').fullCalendar('updateEvent', self.schedules()[pos-1]);
                        //$('#schedulerCalendar').fullCalendar('addEventSource', item);
                    }
                    //$('#schedulerCalendar').fullCalendar('refetchEvents');
                }
                else
                {
                    //TODO error to user
                    console.log('Unable to add new schedule');
                }
                //console.log('schedules len after add '+self.schedules().length);
            });
        }
        else
        {
            //TODO log error to say schedule is not valid
            console.log('invalid schedule');
        }
    };

    //update schedule
    this.updateSchedule = function(oldSched, newSched, infos, revertFunc) {
        //console.log('schedules len before update '+self.schedules().length);
        //prepare content
        var content = {
            uuid: self.agoschedulerUuid,
            command: 'updSchedule',
            schedule: {
                id: oldSched.id,
                title: newSched.title,
                dateStart: moment(newSched.start).format(),
                dateEnd: moment(newSched.end).format(),
                uuidStart: newSched.uuidStart,
                uuidEnd: newSched.uuidEnd,
                color: newSched.color,
                repeat: newSched.repeat
            },
            infos: infos
        }
            
        //update on server
        sendCommand(content, function(res) {
            if( res!==undefined && res.result.result!==undefined && res.result.result.error==0 )
            {
                if( newSched.repeat!=0 )
                {
                    //search all events to refresh
                    for( var i=0; i<self.schedules().length; i++)
                    {
                        if( self.schedules()[i].id==newSched.id )
                        {
                            oldSched.title = newSched.title;
                            //oldSched.start = moment(newSched.start).format();
                            //oldSched.end = moment(newSched.end).format();
                            oldSched.uuidStart = newSched.uuidStart;
                            oldSched.uuidEnd = newSched.uuidEnd;
                            oldSched.color = newSched.color;
                            $('#schedulerCalendar').fullCalendar('updateEvent', self.schedules()[i]);
                        }
                    }
                }
                else
                {
                    //refresh single event
                    oldSched.title = newSched.title;
                    //oldSched.start = moment(newSched.start).format();
                    //oldSched.end = moment(newSched.end).format();
                    oldSched.uuidStart = newSched.uuidStart;
                    oldSched.uuidEnd = newSched.uuidEnd;
                    oldSched.color = newSched.color;
                    //oldSched.repeat = newSched.repeat;
                    $('#schedulerCalendar').fullCalendar('updateEvent', oldSched);
                    //$('#schedulerCalendar').fullCalendar('refetchEvents');
                }
            }
            else
            {
                //TODO error to user
                //revert js if possible
                if( revertFunc!==undefined )
                    revertFunc();
                console.log('Unable to update schedule');
            }
            //console.log('schedules len after update '+self.schedules().length);
        });
    };

    //delete schedule
    this.deleteSchedule = function(sched) {
        //console.log('schedules len before delete '+self.schedules().length);
        var ind = self.schedules.indexOf(sched);
        if( ind!=-1 )
        {
            //prepare content
            var content = {
                uuid: self.agoschedulerUuid,
                command: 'delSchedule',
                id: sched.id
            };

            //remove from server
            sendCommand(content, function(res) {
                if( res!==undefined && res.result.result!==undefined && res.result.result.error==0 )
                {
                    if( sched.repeat!=0 )
                    {
                        //search all events to refresh
                        for( var i=self.schedules().length-1; i>=0; i-- )
                        {
                            if( self.schedules()[i].id==sched.id )
                            {
                                //remove it from list
                                self.schedules.splice(i,1);
                            }
                        }
                    }
                    else
                    {
                        //remove it from list
                        self.schedules.splice(ind,1);
                    }
                    //and remove it/them from fullcalendar
                    $('#schedulerCalendar').fullCalendar('removeEvents', sched.id);
                }
                else
                {
                    //TODO error to user
                    console.log('Unable to delete schedule');
                }
                //console.log('schedules len after delete '+self.schedules().length);
            });
        }
        else
        {
            //TODO log error to say schedule is not valid
            console.log('event not found! unable to delete');
        }
    };

    //open schedule popup
    this.colorPicker = undefined;
    this.openSchedulePopup = function(params) {
        var buttons = [];
        var title;
        if( params.type=='select' )
        {
            //select event
            self.enableRepeat(true);
            
            //set popup values
            self.scheduleStart(params.start);
            self.scheduleEnd(params.end);
            self.selectedRepeat(0);
            title = "Add new schedule";

            //set popup buttons
            buttons.push({
                text: "Add new schedule",
                click: function() {
                    self.addSchedule({
                        start:params.start,
                        end:params.end,
                        repeat:self.selectedRepeat(),
                        scenarioStart:self.selectedStartScenario(),
                        scenarioEnd:self.selectedEndScenario(),
                        color:self.selectedColor()
                    });
                    $(this).dialog('close');
                }
            });
        }
        else if( params.type=='click' )
        {
            //click event
            self.enableRepeat(false);

            //set popup values
            self.scheduleStart(params.event.start);
            self.scheduleEnd(params.event.end);
            for( var i=0; i<self.availableStartScenarios().length; i++)
            {
                if( self.availableStartScenarios()[i].value==params.event.uuidStart )
                    self.selectedStartScenario(self.availableStartScenarios()[i]);
            }
            for( var i=0; i<self.availableEndScenarios().length; i++)
            {
                if( self.availableEndScenarios()[i].value==params.event.uuidEnd )
                {
                    self.selectedEndScenario(self.availableEndScenarios()[i]);
                }
            }
            self.selectedRepeat(params.event.repeat);
            self.selectedColor(params.event.color);
            title = "Update schedule";

            //set popup buttons
            buttons.push({
                text: "Update schedule",
                click: function() {
                    //prepare data for update
                    var newSched = {
                        id: params.event.id,
                        title: self.selectedStartScenario().text+'-'+self.selectedEndScenario().text,
                        start: params.event.start,
                        end: params.event.end,
                        uuidStart: self.selectedStartScenario().value,
                        uuidEnd: self.selectedEndScenario().value,
                        color: self.selectedColor(),
                        repeat: self.selectedRepeat()
                    };
                    self.updateSchedule(params.event, newSched, {type:'update', days:0, minutes:0}, undefined);
                    $(this).dialog('close');
                }
            });
            buttons.push({
                text: "Delete schedule",
                click: function() {
                    if( confirm("Delete this schedule?") )
                    {
                        self.deleteSchedule(params.event);
                        $(this).dialog('close');
                    }
                }
            });
        }

        //add cancel button
        buttons.push({
            text: "Cancel",
            click: function() {
                $(this).dialog('close');
            }
        });

        //init color picker
        if( self.colorPicker===undefined )
        {
            self.colorPicker  = new jscolor.color(document.getElementById('schedulerColorPicker'), {pickerClosable:true, hash:true});
        }
        if( params.event!==undefined )
        {
            self.colorPicker.fromString( params.event.color );
        }

        //open popup
        $( "#schedulerDialog" ).dialog({
            title: title,
            height: 350,
            width: 600,
            modal: true,
            buttons: buttons
        });
    };

    //event when selection on calendar occured
    self.selectSchedule = function(start, end, jsEvent, view) {
        var select = {
            type: 'select',
            start: start,
            end: end,
            jsEvent: jsEvent,
            view: view
        };
        self.openSchedulePopup(select);
    }
    
    //event when schedule is clicked on calendar
    self.clickSchedule = function(event, jsEvent, view) {
        var click = {
            type: 'click',
            event: event,
            jsEvent: jsEvent,
            view: view
        };
        self.openSchedulePopup(click);
    }

    //event when schedule is resized on calendar
    self.resizeSchedule = function(event, daysOffset, minutesOffset, revertFunc, jsEvent, ui, view) {
        self.updateSchedule(event, event, {type:'resize', days:daysOffset, minutes:minutesOffset}, revertFunc);
    }

    //event when schedule is dropped on calendar
    self.dropSchedule = function(event, daysOffset, minutesOffset, revertFunc, jsEvent, ui, view) {
        self.updateSchedule(event, event, {type:'drop', days:daysOffset, minutes:minutesOffset}, revertFunc);
    }

    //calendar view model
    this.calendarViewModel = new ko.fullCalendar.viewModel({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        slotMinutes: 15,
        defaultView: 'agendaWeek',
        allDaySlot: false,
        viewDate: self.viewDate,
        selectable: true,
        selectHelper: true,
        editable: true,
        events: self.schedules,
        select: self.selectSchedule,
        eventClick: self.clickSchedule,
        eventResize: self.resizeSchedule,
        eventDrop: self.dropSchedule
    });

    //get all schedules
    this.getSchedules();
}

/**
 * Entry point: mandatory!
 */
function init_plugin()
{
    ko.fullCalendar = {
        // Defines a view model class you can use to populate a calendar
        viewModel: function(configuration) {
            this.selectable = configuration.selectable;
            this.selecHelper = configuration.selectHelper;
            this.select = configuration.select;
            this.events = configuration.events;
            this.header = configuration.header;
            this.allDaySlot = configuration.allDaySlot;
            this.editable = configuration.editable;
            this.viewDate = configuration.viewDate || ko.observable(new Date());
            this.defaultView = configuration.defaultView;
            this.eventClick = configuration.eventClick;
            this.eventResize = configuration.eventResize;
            this.eventDrop = configuration.eventDrop;
            this.slotMinutes = configuration.slotMinutes;
        }
    };

    // The "fullCalendar" binding
    ko.bindingHandlers.fullCalendar = {
        // This method is called to initialize the node, and will also be called again if you change what the grid is bound to
        update: function(element, viewModelAccessor) {
            var viewModel = viewModelAccessor();
            element.innerHTML = "";
            var now = new Date();

            $(element).fullCalendar({
                events: ko.utils.unwrapObservable(viewModel.events),
                header: viewModel.header,
                allDaySlot: viewModel.allDaySlot,
                editable: viewModel.editable,
                selectable: viewModel.selectable,
                selectHelper: viewModel.selectHelper,
                select: viewModel.select,
                defaultView: viewModel.defaultView,
                eventClick: viewModel.eventClick,
                eventResize: viewModel.eventResize,
                eventDrop: viewModel.eventDrop,
                slotMinutes: viewModel.slotMinutes,
                scrollTime: now.getHours()+':'+now.getMinutes()+':'+now.getSeconds()
            });
            $(element).fullCalendar('gotoDate', ko.utils.unwrapObservable(viewModel.viewDate));
            //ko.utils.unwrapObservable(viewModel.viewDate);
            //var now = ''+viewModel.viewDate.getHours()+':'+viewModel.viewDate.getMinutes()+':'+viewModel.viewDate.getSeconds();
            //$(element).fullCalendar('scrollTime', now);
            //console.log(now.getHours()+':'+now.getMinutes()+':'+now.getSeconds());
        }
    };

    model = new agoSchedulerPlugin(deviceMap);
    model.mainTemplate = function() {
    	return templatePath + "agoscheduler";
    }.bind(model);
    ko.applyBindings(model);
}
