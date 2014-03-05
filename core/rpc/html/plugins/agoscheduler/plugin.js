/**
 * Agoscheduler plugin
 * @returns {agoscheduler}
 */
function agoSchedulerPlugin(deviceMap) {
    //members
    var self = this;
    this.viewDate = ko.observable(new Date());
    this.hasNavigation = ko.observable(false);
    this.schedules = [];
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
            if( res!==undefined && res.result!==undefined && res.result!=='no-reply')
            {
                for( var i=0; i<res.result.schedules.length; i++)
                {
                    //convert UTC datetimes to local datetimes
                    res.result.schedules[i].start = $.fullCalendar.parseISO8601(res.result.schedules[i].start);
                    res.result.schedules[i].end = $.fullCalendar.parseISO8601(res.result.schedules[i].end);
                    //add schedule
                    self.schedules.push(res.result.schedules[i]);
                }
                $('#schedulerCalendar').fullCalendar('refetchEvents');
            }
            else
            {
                notif.error('#nr', 0);
                console.log('unable to get schedules list');
            }
        });
    };

    //add new schedule
    //recurring schedules are computed server-side
    this.addSchedule = function(sched) {
        if( sched.scenarioStart!==undefined && sched.scenarioEnd!==undefined )
        {
            var content = {
                uuid: self.agoschedulerUuid,
                command: "addSchedule",
                title: sched.scenarioStart.text + '-' + sched.scenarioEnd.text,
                uuidStart: sched.scenarioStart.value,
                uuidEnd: sched.scenarioEnd.value,
                dateStart: sched.start,
                dateEnd: sched.end,
                color: sched.color,
                repeat: sched.repeat
            };

            //send new schedule to controller
            sendCommand(content, function(res) {
                if( res!==undefined && res.result!==undefined && res.result!=='no-reply' && res.result.error==0 )
                {
                    //and add all new schedules to fullCalendar
                    for( var i=0; i<res.result.schedules.length; i++)
                    {
                        //convert UTC datetime to local datetime
                        res.result.schedules[i].start = $.fullCalendar.parseISO8601(res.result.schedules[i].start);
                        res.result.schedules[i].end = $.fullCalendar.parseISO8601(res.result.schedules[i].end);
                        self.schedules.push(res.result.schedules[i]);
                    }
                    $('#schedulerCalendar').fullCalendar('refetchEvents');
                    notif.success('#a');
                }
                else
                {
                    notif.error('#na');
                    console.log('Unable to add new schedule');
                }
            });
        }
        else
        {
            notif.error('#ie');
            console.log('invalid schedule');
        }
    };

    //update schedule
    this.updateSchedule = function(oldSched, newSched, infos, revertFunc) {
        //prepare content
        var content = {
            uuid: self.agoschedulerUuid,
            command: 'updSchedule',
            schedule: {
                id: oldSched.id,
                title: newSched.title,
                dateStart: newSched.start,
                dateEnd: newSched.end,
                uuidStart: newSched.uuidStart,
                uuidEnd: newSched.uuidEnd,
                color: newSched.color,
                repeat: newSched.repeat
            },
            infos: infos
        }
            
        //update on server
        sendCommand(content, function(res) {
            if( res!==undefined && res.result!==undefined && res.result!=='no-reply' && res.result.error==0 )
            {
                if( newSched.repeat!=0 )
                {
                    //search all events to refresh
                    for( var i=0; i<self.schedules.length; i++)
                    {
                        if( self.schedules[i].id==newSched.id )
                        {
                            self.schedules[i].title = newSched.title;
                            self.schedules[i].uuidStart = newSched.uuidStart;
                            self.schedules[i].uuidEnd = newSched.uuidEnd;
                            self.schedules[i].color = newSched.color;
                        }
                    }
                }
                else
                {
                    //refresh single event
                    oldSched.title = newSched.title;
                    oldSched.uuidStart = newSched.uuidStart;
                    oldSched.uuidEnd = newSched.uuidEnd;
                    oldSched.color = newSched.color;
                }
                $('#schedulerCalendar').fullCalendar('refetchEvents');
                notif.success('#u');
            }
            else
            {
                //revert js if possible
                notif.error('#nu');
                if( revertFunc!==undefined )
                    revertFunc();
                console.log('Unable to update schedule');
            }
        });
    };

    //delete schedule
    this.deleteSchedule = function(sched) {
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
                if( res!==undefined && res.result!==undefined && res.result!=='no-reply' && res.result.error==0 )
                {
                    if( sched.repeat!=0 )
                    {
                        //search all events to refresh
                        for( var i=self.schedules.length-1; i>=0; i-- )
                        {
                            if( self.schedules[i].id==sched.id )
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
                    notif.success('#d');
                }
                else
                {
                    notif.error('#nd');
                    console.log('Unable to delete schedule');
                }
            });
        }
        else
        {
            notif.error('#ie');
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
    self.selectSchedule = function(start, end, allDay, jsEvent, view) {
        var select = {
            type: 'select',
            start: start,
            end: end,
            jsEvent: jsEvent,
            view: view
        };
        self.openSchedulePopup(select);
        $('#schedulerCalendar').fullCalendar('unselect');
    };
    
    //event when schedule is clicked on calendar
    self.clickSchedule = function(event, jsEvent, view) {
        var click = {
            type: 'click',
            event: event,
            jsEvent: jsEvent,
            view: view
        };
        self.openSchedulePopup(click);
    };

    //event when schedule is resized on calendar
    self.resizeSchedule = function(event, daysOffset, minutesOffset, revertFunc, jsEvent, ui, view) {
        self.updateSchedule(event, event, {type:'resize', days:daysOffset, minutes:minutesOffset}, revertFunc);
    };

    //event when schedule is dropped on calendar
    self.dropSchedule = function(event, daysOffset, minutesOffset, revertFunc, jsEvent, ui, view) {
        self.updateSchedule(event, event, {type:'drop', days:daysOffset, minutes:minutesOffset}, revertFunc);
    };

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
                firstHour: now.getHours()
            });
            $(element).fullCalendar('gotoDate', ko.utils.unwrapObservable(viewModel.viewDate));
        }
    };

    model = new agoSchedulerPlugin(deviceMap);
    model.mainTemplate = function() {
	    return templatePath + "agoscheduler";
    }.bind(model);
    ko.applyBindings(model);
}
