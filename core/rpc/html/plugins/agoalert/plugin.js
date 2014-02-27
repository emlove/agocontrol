/**
 * Agoalert plugin
 * @returns {agoalert}
 */
function agoAlertPlugin(deviceMap) {
    //members
    var self = this;
    self.hasNavigation = ko.observable(false);
    self.gtalkStatus = ko.observable(self.gtalkStatus);
    self.gtalkUsername = ko.observable(self.gtalkUsername);
    self.gtalkPassword = ko.observable(self.gtalkPassword);
    self.smsStatus = ko.observable(self.smsStatus);
    self.twelvevoipUsername = ko.observable(self.twelvevoipUsername);
    self.twelvevoipPassword = ko.observable(self.twelvevoipPassword);
    self.mailStatus = ko.observable(self.mailStatus);
    self.mailSmtp = ko.observable(self.mailSmtp);
    self.mailLogin = ko.observable(self.mailLogin);
    self.mailPassword = ko.observable(self.mailPassword);
    self.mailTls = ko.observable(self.mailTls);
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
    self.agoalertUuid;
    
    //get agoalert uuid
    if( deviceMap!==undefined )
    {
        for( var i=0; i<deviceMap.length; i++ )
        {
            if( deviceMap[i].devicetype=='alertcontroller' )
            {
                self.agoalertUuid = deviceMap[i].uuid;
            }
        }
    }

    //get current status
    self.getAlertsConfigs = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'status';
        sendCommand(content, function(res) {
            self.gtalkStatus(true);
            if (res.result.gtalk.configured)
            {
                self.gtalkUsername(res.result.gtalk.username);
                self.gtalkPassword(res.result.gtalk.password);
            }
            self.mailStatus(res.result.mail.configured);
            if (res.result.mail.configured)
            {
                self.mailSmtp(res.result.mail.smtp);
                self.mailLogin(res.result.mail.login);
                self.mailPassword(res.result.mail.password);
                if (res.result.mail.tls == 1)
                    self.mailTls(true);
                else
                    self.mailTls(false);
                self.mailSender(res.result.mail.sender);
            }
            self.smsStatus(res.result.sms.configured);
            if (res.result.sms.configured)
            {
                self.twelvevoipUsername(res.result.sms.username);
                self.twelvevoipPassword(res.result.sms.password);
            }
            self.twitterStatus(res.result.twitter.configured);
            self.pushStatus(res.result.push.configured);
            if (res.result.push.configured)
            {
                self.selectedPushProvider(res.result.push.provider);
                if (res.result.push.provider == 'pushbullet')
                {
                    self.pushbulletApikey(res.result.push.apikey);
                    self.pushbulletAvailableDevices(res.result.push.devices);
                    self.pushbulletSelectedDevices(res.result.push.devices);
                }
                else if (res.result.push.provider == 'pushover')
                {
                    self.pushoverUserid(res.result.push.userid);
                }
                else if (res.result.push.provider == 'notifymyandroid')
                {
                    self.nmaAvailableApikeys(res.result.push.apikeys);
                }
            }
        });
    };

    this.twitterUrl = function()
    {
        el = document.getElementsByClassName("twitterUrl");
        el[0].innerHTML = 'Generating url...';
        //get authorization url
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'twitter';
        content.param2 = '';
        sendCommand(content, function(res) {
            if (res.result.error == 0)
            {
                //display link
                el[0].innerHTML = '<a href="' + res.result.url + '" target="_blank">authorization url</a>';
            }
            else
            {
                alert('Unable to get Twitter url.');
            }
        });
    };

    this.twitterAccessCode = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'twitter';
        content.param2 = document.getElementsByClassName("twitterCode")[0].value;
        sendCommand(content, function(res) {
            if (res.result.error == 1)
            {
                alert(res.result.msg);
            }
            self.getAlertsConfigs();
        });
    };

    this.twitterTest = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'test';
        content.param1 = 'twitter';
        sendCommand(content, function(res) {
            alert(res.result.msg);
        });
    };

    this.smsConfig = function() {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'sms';
        content.param2 = self.smsUsername();
        content.param3 = self.smsPassword();
        sendCommand(content, function(res) {
            if (res.result.error == 1)
            {
                alert(res.result.msg);
            }
            self.getAlertsConfigs();
        });
    };

    this.smsTest = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'test';
        content.param1 = 'sms';
        sendCommand(content, function(res) {
            alert(res.result.msg);
        });
    };

    this.gtalkConfig = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'gtalk';
        content.param2 = self.gtalkUsername();
        content.param3 = self.gtalkPassword();
        sendCommand(content, function(res) {
            if (res.result.error == 1)
            {
                alert(res.result.msg);
            }
            self.getAlertsConfigs();
        });
    };

    this.gtalkTest = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'test';
        content.param1 = 'gtalk';
        sendCommand(content, function(res) {
            alert(res.result.msg);
        });
    };

    this.mailConfig = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'mail';
        content.param2 = self.mailSmtp();
        content.param3 = self.mailSender();
        content.param4 = self.mailLogin() + '%_%' + self.mailPassword();
        content.param5 = '0';
        if (self.mailTls())
        {
            content.param5 = '1';
        }
        sendCommand(content, function(res) {
            if (res.result.error == 1)
            {
                alert(res.result.msg);
            }
            self.getAlertsConfigs();
        });
    };

    this.mailTest = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'test';
        content.param1 = 'mail';
        content.param2 = document.getElementsByClassName("mailEmail")[0].value;
        sendCommand(content, function(res) {
            alert(res.result.msg);
        });
    };

    this.pushbulletRefreshDevices = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'push';
        content.param2 = this.selectedPushProvider();
        content.param3 = 'getdevices';
        content.param4 = self.pushbulletApikey();
        sendCommand(content, function(res) {
            if (res.result.error == 0)
            {
                self.pushbulletAvailableDevices(res.result.devices);
            }
            else
            {
                //TODO error
            }
        });
    };

    this.nmaAddApikey = function()
    {
        if (self.nmaApikey().length > 0)
        {
            self.nmaAvailableApikeys.push(self.nmaApikey());
        }
        self.nmaApikey('');
    };

    this.nmaDelApikey = function()
    {
        for ( var j = self.nmaSelectedApikeys().length - 1; j >= 0; j--)
        {
            for ( var i = self.nmaAvailableApikeys().length - 1; i >= 0; i--)
            {
                if (self.nmaAvailableApikeys()[i] === self.nmaSelectedApikeys()[j])
                {
                    self.nmaAvailableApikeys().splice(i, 1);
                }
            }
        }
        self.nmaAvailableApikeys(self.nmaAvailableApikeys());
    };

    this.pushConfig = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'setconfig';
        content.param1 = 'push';
        content.param2 = this.selectedPushProvider();
        if (this.selectedPushProvider() == 'pushbullet')
        {
            content.param3 = 'save';
            content.param4 = this.pushbulletApikey();
            content.param5 = this.pushbulletSelectedDevices();
        }
        else if (this.selectedPushProvider() == 'pushover')
        {
            content.param3 = this.pushoverUserid();
        }
        else if (this.selectedPushProvider() == 'notifymyandroid')
        {
            content.param3 = this.nmaAvailableApikeys();
        }
        sendCommand(content, function(res) {
            if (res.result.error == 1)
            {
                alert(res.result.msg);
            }
            self.getAlertsConfigs();
        });
    };

    this.pushTest = function()
    {
        var content = {};
        content.uuid = self.agoalertUuid;
        content.command = 'test';
        content.param1 = 'push';
        sendCommand(content, function(res) {
            alert(res.result.msg);
        });
    };
}

/**
 * Entry point: mandatory!
 */
function init_plugin()
{
    ko.bindingHandlers.jqTabs = {
        init: function(element, valueAccessor) {
            //init
            var options = valueAccessor() || {};
            setTimeout( function() { $(element).tabs(options); }, 0);
            //load config
            model.getAlertsConfigs();
        }
    };

    model = new agoAlertPlugin(deviceMap);
    model.mainTemplate = function() {
	    return templatePath + "agoalert";
    }.bind(model);
    ko.applyBindings(model);
}
