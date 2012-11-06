function add_scenario_command(command) {
    var intId = $("#scenario_builder_fieldset div").length + 1;
    var fieldWrapper = $("<div class=\"fieldwrapper\" id=\"field" + intId + "\"/>");
    var Devices = $("#scenario_device_options").html();
    var removeButton = $("<input type=\"button\" class=\"remove\" value=\"-\" />");
    var scommand = $('<select />');
    removeButton.click(function () {
        $(this).parent().remove();
    });
    fieldWrapper.append(removeButton);
    fieldWrapper.append(Devices);
    $("#scenario_builder_fieldset").append(fieldWrapper);

    var current = document.getElementsByClassName("scenario_device_select")[document.getElementsByClassName("scenario_device_select").length - 1];

    $("#scommand").live("change", function () {
        var input_setlevel = $("<input class=\"isetlevel\" commands=\"isetlevel\" name=\"inputsetlevel\" id=\"inputsetlevel\" />");
        $(this).parent().find(".isetlevel").remove();
        if ($('option:selected', this).text() == "setlevel") {
            $(this).parent().append(input_setlevel);
            if (command.level !== undefined) {
                input_setlevel.val(command.level);
            }
        }
    });

    $(current).live("change", function () {
        var scommand = $('<select class=\"scommand\" id=\"scommand\" />');
        var input_sleep = $("<input commands=\"sleep\" name=\"sleep\" id=\"sleep\" />");

        $(this).parent().find(".scommand").remove();
        $(this).parent().find(".sleep").remove();
        $(this).parent().find(".isetlevel").remove();

        if ($('option:selected', this).attr("commands").match(/on/)) {
            $('<option />', {
                value: "on",
                text: "on"
            }).appendTo(scommand);
        }
        if ($('option:selected', this).attr("commands").match(/off/)) {
            $('<option />', {
                value: "off",
                text: "off"
            }).appendTo(scommand);
        }
        if ($('option:selected', this).attr("commands").match(/setlevel/)) {
            $('<option />', {
                value: "setlevel",
                text: "setlevel"
            }).appendTo(scommand);
        }
        if ($('option:selected', this).attr("commands").match(/isleep/)) {
            if (command.delay !== undefined) {
                input_sleep.val(command.delay);
            }
            $(this).parent().append(input_sleep);
        }

        if (command.command !== undefined) {
            scommand.val(command.command);
        }

        $(this).parent().append(scommand);
        $(scommand).trigger("change");
        $('select:not(:has(option))').remove();
    });


    var opts = current.options;
    for (var i = 0; i < opts.length; i++) {
        if (command.uuid == opts[i].getAttribute("rel")) {
            opts[i].selected = true;
        }
    }
    
    $(current).trigger("change");    

}

$(document).ready(function () {

    $(".switch_on").click(function (event) {
        var rel = $(this).attr('rel');
        $.ajax({
            type: "GET",
            url: "/command/" + rel + "/on"
        });
    });

    $(".switch_off").click(function (event) {
        var rel = $(this).attr('rel');
        $.ajax({
            type: "GET",
            url: "/command/" + rel + "/off"
        });
    });

    $(".delete_room").click(function (event) {
        var rel = $(this).attr('rel');
        $.ajax({
            type: "GET",
            url: "/deleteroom/" + rel,
            success: function (data) {
                window.location.reload();
            }
        });
    });

    $(".scenario_delete").click(function (event) {
        var rel = $(this).attr('rel');
        $.ajax({
            type: "GET",
            url: "/deletescenario/" + rel,
            success: function (data) {
                window.location.reload();
            }

        });
    });

    $(".scenario_edit").click(function (event) {
        var rel = $(this).attr('rel');
        document.location.href = "/editscenario?uuid=" + rel;
    });

    $(".new_room").click(function (event) {
        var rel = $("#new_room_name").attr("value");
        $.ajax({
            type: "GET",
            url: "/createroom/" + rel,
            success: function (data) {
                console.log(data);
                window.location.reload();

            }
        });
    });

    $(".event_edit").click(function (event) {
        var rel = $(this).attr('rel');
        document.location.href = "/event/edit?uuid=" + rel;
    });

    $(".event_delete").click(function (event) {
        var rel = $(this).attr('rel');
        $.ajax({
            type: "GET",
            url: "/event/delete?uuid=" + rel,
            success: function (data) {
                window.location.reload();
            }

        });
    });


    // comic buttons toogle
    $(".switch").click(function (event) {
        var rel = $(this).attr('rel');
        if ($(this).attr("class") == "switch off") {
            $.ajax({
                type: "GET",
                url: "/command/" + rel + "/on"
            });
            $(this).attr("class", "switch on");
        } else {
            $(this).attr("class", "switch off");
            $.ajax({
                type: "GET",
                url: "/command/" + rel + "/off"
            });
        }
    });

    // dimmer section
    var dimmer = $('#dimmer');

    //Call the dimmer
    dimmer.slider({
        //Config
        range: "min",
        min: 1,
        value: 10,

        //Dimmer Event
        slide: function (event, ui) { //When the dimmer is sliding

            var value = dimmer.slider('value'),
                level = $('.level');

            if (value <= 5) {
                level.css('background-position', '0 -640px');
            } else if (value <= 10) {
                level.css('background-position', '0 -576px');
            } else if (value <= 20) {
                level.css('background-position', '0 -512px');
            } else if (value <= 30) {
                level.css('background-position', '0 -448px');
            } else if (value <= 40) {
                level.css('background-position', '0 -384px');
            } else if (value <= 50) {
                level.css('background-position', '0 -320px');
            } else if (value <= 60) {
                level.css('background-position', '0 -256px');
            } else if (value <= 70) {
                level.css('background-position', '0 -192px');
            } else if (value <= 80) {
                level.css('background-position', '0 -128px');
            } else if (value <= 90) {
                level.css('background-position', '0 -64px');
            } else {
                level.css('background-position', '0 0');
            };

        }

    });


    // Device and Room Setup - enable table sorter
    $("#DeviceSetup").tablesorter();
    $("#RoomSetup").tablesorter();


    // Device and Room Setup - edit in place 

    $(".edit_room").click(function (event) {
        var rel = $(this).attr('rel');
        $(this).editable('/setroomname/submit/', {
            name: 'roomname',
            submitdata: {
                uuid: rel
            },
            cancel: 'Cancel',
            submit: 'OK',
            indicator: 'Saving...',
            tooltip: 'Click to edit...'
        });
    });

    $(".edit_device").click(function (event) {
        var rel = $(this).attr('rel');
        $(this).editable('/setdevicename/submit/', {
            name: 'devicename',
            submitdata: {
                uuid: rel
            },
            cancel: 'Cancel',
            submit: 'OK',
            indicator: 'Saving...',
            tooltip: 'Click to edit...'
        });
    });

    $(".select_device_room").click(function (event) {
        var rel = $(this).attr('rel');
        $(this).editable('/setdeviceroom/submit/', {
            loadurl: '/get_rooms/',
            type: 'select',
            name: 'deviceroom',
            submitdata: {
                uuid: rel
            },
            cancel: 'Cancel',
            submit: 'OK',
            indicator: 'Saving...',
            tooltip: 'Click to edit...',
            callback: function (value, settings) {
                window.location.reload();
            }
        });

    });

    // Device Slider Setup

    $(".slider").each(function () {
        $(this).empty().slider({
            value: $(this).attr('def_value'),
            min: 0,
            max: 100,
            step: 5,
            stop: function (event, ui) {
                var value = ui.value;
                var rel = $(this).attr('rel');
                var call_url = "/setdevicelevel/" + rel + "/setlevel/" + value
                $.ajax({
                    //The request type is set to GET, alternatively, it could be POST if we were passing data. 
                    type: "GET",
                    //The url is set to our request path.
                    url: call_url,
                });
            }
        });
    });


    var copyHelper = null;

    $("#scenario_drag, #scenario_drop").sortable({
        connectWith: ".connectedSortable",
        forcePlaceholderSize: true,
        helper: function (e, li) {
            if (li.parents().attr('id') == 'scenario_drop') {
                copyHelper = li;
                return li;
            } else {
                copyHelper = li.clone().insertAfter(li);
                return li.clone();
            }
        },
        stop: function () {
            copyHelper && copyHelper.remove();
        },
        receive: function (e, li) {
            if (li.sender.attr('id') == 'scenario_drop') {
                li.item.remove();
            } else {
                copyHelper = null;
            }

            var droppedElemTxt = $(li.item).text();
            var scommand = $('<select />');
            var input_setlevel = $("<input name=\"setlevel\" />");
            if ($(li.item).attr("commands").match(/on/)) {
                $('<option />', {
                    value: "on",
                    text: "on"
                }).appendTo(scommand);
            }
            if ($(li.item).attr("commands").match(/off/)) {
                $('<option />', {
                    value: "off",
                    text: "off"
                }).appendTo(scommand);
            }
            if ($(li.item).attr("commands").match(/setlevel/)) {
                $('<option />', {
                    value: "setlevel",
                    text: "setlevel"
                }).appendTo(scommand);
                // append('<input type="text" name="myinput'+i+'" />');
                $(li.item).append(input_setlevel);
            }
            $(li.item).append(scommand);

        }
    }).disableSelection();



    $(".submit_scenario").click(function (event) {
        // build list to send
        var list = new Array();
        $("#scenario_drop li").each(function (index) {
            //list.push( {'index':index, 'uuid':$(this).attr('rel'), 'name':$(this).text(), 'command': $("option:selected", this).text() } );	
            //list.push( {'index':index, 'uuid':$(this).attr('rel'), 'command': $("option:selected", this).text() } );	
            list.push({
                'uuid': $(this).attr('rel'),
                'command': $("option:selected", this).text()
            });
        });
        $.ajax({
            type: "POST",
            url: '/createscenario',
            //dataType: 'json',
            async: false,
            //data: {'json': list}
            data: JSON.stringify(list),
            contentType: "application/json; charset=utf-8",
            traditional: true
        })

    });

    // Scenario builder 2.0
    $(document).ready(function () {
        $("#scenario_add_command").click(function () {
            var intId = $("#scenario_builder_fieldset div").length + 1;
            var fieldWrapper = $("<div class=\"fieldwrapper\" id=\"field" + intId + "\"/>");
            var Devices = $("#scenario_device_options").html();
            var removeButton = $("<input type=\"button\" class=\"remove\" value=\"-\" />");
            var scommand = $('<select />');
            removeButton.click(function () {
                $(this).parent().remove();
            });
            fieldWrapper.append(removeButton);
            fieldWrapper.append(Devices);
            $("#scenario_builder_fieldset").append(fieldWrapper);
        });
    });

    $(document).ready(function () {
        $("#scenario_add_command2").click(function () {
            var intId = $("#scenario_builder_fieldset div").length + 1;
            var fieldWrapper = $("<div class=\"fieldwrapper\" id=\"field" + intId + "\"/>");
            var Devices = $("#scenario_device_options2").html();
            var removeButton = $("<input type=\"button\" class=\"remove\" value=\"-\" />");
            var scommand = $('<select />');
            removeButton.click(function () {
                $(this).parent().remove();
            });
            fieldWrapper.append(removeButton);
            fieldWrapper.append(Devices);
            $("#scenario_builder_fieldset").append(fieldWrapper);
        });
    });

    $('#scenario_device_select').live("change", function () {
        var scommand = $('<select class=\"scommand\" id=\"scommand\" />');
        var input_sleep = $("<input class=\"sleep\" commands=\"sleep\" name=\"sleep\" id=\"sleep\" />");

        $(this).parent().find(".scommand").remove();
        $(this).parent().find(".isetlevel").remove();
        $(this).parent().find(".sleep").remove();

        if ($('option:selected', this).attr("commands").match(/on/)) {
            $('<option />', {
                value: "on",
                text: "on"
            }).appendTo(scommand);
        }
        if ($('option:selected', this).attr("commands").match(/off/)) {
            $('<option />', {
                value: "off",
                text: "off"
            }).appendTo(scommand);
        }
        if ($('option:selected', this).attr("commands").match(/setlevel/)) {
            $('<option />', {
                value: "setlevel",
                text: "setlevel"
            }).appendTo(scommand);
        }
        if ($('option:selected', this).attr("commands").match(/isleep/)) {
            $(this).parent().append(input_sleep);
        }

        $(this).parent().append(scommand);
        $('select:not(:has(option))').remove();
    })
        .change();

    $("#scommand").live("change", function () {
        var input_setlevel = $("<input class=\"isetlevel\" commands=\"isetlevel\" name=\"inputsetlevel\" id=\"inputsetlevel\" />");
        $(this).parent().find(".isetlevel").remove();
        if ($('option:selected', this).text() == "setlevel") {
            $(this).parent().append(input_setlevel);
        }
    });

    $("#edit_scenario2").click(function (event) {
        // build list to send
        var scenario = [];
        var scenario_name = $('#scenario_name').val();
        //	alert(scenario_name);
        $("#scenario_builder_fieldset div").each(function (index) {
            var uuid = $(this).find('option:selected').first().attr('rel');
            var command = $(this).find("select#scommand").first().val();
            //alert($(this).find('option:selected').first().attr('rel'));
            //alert($(this).find("select#scommand").first().val());
            if ($(this).find('option:selected').first().attr('commands') == "isleep") {
                var sleep = $(this).find("input#sleep").first().val();
                scenario.push({
                    'uuid': uuid,
                    'command': 'scenariosleep',
                    'delay': sleep
                });
            } else if (command == "setlevel") {
                var setlevel = $(this).find("input#inputsetlevel").first().val();
                scenario.push({
                    'uuid': uuid,
                    'command': command,
                    'level': setlevel
                });
            } else {
                scenario.push({
                    'uuid': uuid,
                    'command': command
                });
            }
        });

        var devNode = "name=" + encodeURIComponent(scenario_name) + "&uuid=" + encodeURIComponent($('#uuid').val())
                       + "&commands=" + encodeURIComponent(JSON.stringify(scenario));
        
        res = $.ajax({
            type: "POST",
            url: '/editscenario/doEdit',
            async: false,
            data: devNode,
            contentType: "application/x-www-form-urlencoded",
            traditional: true
        });
        if (res.responseText == "OK") {
            document.location.href = "/scenario";
        }
        else {
            alert("Edit failed!");
        }

    });

    $("#submit_scenario2").click(function (event) {
        // build list to send
        var scenario = new Array();
        var scenario_name = $('#scenario_name').val();
        //	alert(scenario_name);
        $("#scenario_builder_fieldset div").each(function (index) {
            var uuid = $(this).find('option:selected').first().attr('rel');
            var command = $(this).find("select#scommand").first().val();
            //alert($(this).find('option:selected').first().attr('rel'));
            //alert($(this).find("select#scommand").first().val());
            if ($(this).find('option:selected').first().attr('commands') == "isleep") {
                var sleep = $(this).find("input#sleep").first().val();
                scenario.push({
                    'uuid': uuid,
                    'command': 'scenariosleep',
                    'delay': sleep
                });
            } else if (command == "setlevel") {
                var setlevel = $(this).find("input#inputsetlevel").first().val();
                scenario.push({
                    'uuid': uuid,
                    'command': command,
                    'level': setlevel
                });
            } else {
                scenario.push({
                    'uuid': uuid,
                    'command': command
                });
            }
        });

        var res = $.ajax({
            type: "POST",
            url: '/createscenario',
            //dataType: 'json',
            async: false,
            //data: {'json': list}
            data: JSON.stringify(scenario),
            contentType: "application/json; charset=utf-8",
            traditional: true
        });

        var devNode = "devicename=" + scenario_name + "&uuid=" + res.responseText + "&id=0";

        res = $.ajax({
            type: "POST",
            url: '/setdevicename/submit',
            async: false,
            data: devNode,
            traditional: true
        });


        document.location.href = "/scenario";

    });

});
