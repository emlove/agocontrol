// IIFE - Immediately Invoked Function Expression
(function(yourcode) {

    // The global jQuery object is passed as a parameter
  	yourcode(window.jQuery, window, document);

} (function($, window, document) {
    // The $ is now locally scoped 

    // Listen for the jQuery ready event on the document
    $(function() {
        // The DOM is ready!
        notif = new agoNotifications();
        notif.init();
    });
    
    //The DOM may not be ready
    var NOTIF_INFO = 0;
    var NOTIF_SUCC = 1;
    var NOTIF_WARN = 2;
    var NOTIF_ERRO = 3;
    var NOTIF_FATA = 4;

    function agoNotifications() {
        //members
        var self = this;
        self.name = "notification-box";
        self.duration = 4; //seconds
    
        //create main container
        self.init = function() {
            self.container = $("<div></div>");
            self.container.css({
                "width":"100%",
                "top":"0px",
                "left":"0px",
                "z-index":"1000",
                "position":"fixed"
            }).attr("name", self.name);
            self.container.appendTo($(document.body));
        };
    
        //notify message (internal use)
        self._notify = function(message, type, duration) {
            if( self.container!==undefined )
            {
                if( typeof duration=='undefined' )
                    duration = self.duration;
                if( typeof message=='string' && message.charAt(0)=="#" )
                    message = $(message).html();
                var msg = new agoNotificationMessage();
                msg.init(self.container, message, type, duration);
                msg.show();
            }
            else
            {
                console.log('container is undefined');
            }
        };
    
        //notify info message
        self.info = function(message, duration) {
            self._notify(message, NOTIF_INFO, duration);
        };
        
        //notify success message
        self.success = function(message, duration) {
            self._notify(message, NOTIF_SUCC, duration);
        };
        
        //notify warning message
        self.warning = function(message, duration) {
            self._notify(message, NOTIF_WARN, duration);
        };
        
        //notify error message
        self.error = function(message, duration) {
            self._notify(message, NOTIF_ERRO, duration);
        };

        //notify fatal message
        self.fatal = function(message) {
            self._notify(message, NOTIF_FATA, 0);
        };
    };

    function agoNotificationMessage() {
        //members
        var self = this;
        
        //init
        self.init = function(container, message, type, duration) {
            self.container = container;
            self.message = message;
            self.type = type;
            self.duration = duration*1000;
        };
        
        //show notification
        self.show = function() {
            //build elem
            self.elem = $("<div></div>").css("margin-bottom", "0px");
            if( self.type==NOTIF_SUCC )
                self.elem.attr("class", "success alert");
            else if( self.type==NOTIF_ERRO )
                self.elem.attr("class", "danger alert");
            else if( self.type==NOTIF_WARN )
                self.elem.attr("class", "warning alert");
            else if( self.type==NOTIF_FATA )
                self.elem.attr("class", "info alert");
            else
                self.elem.attr("class", "primary alert");
            //build close
            self.close = $("<i></i>");
            self.close.attr("class", "icon-cancel-circled").css("cursor", "pointer").click(function() { self.hide(); });
            //build msg
            self.msg = $("<span></span>");
            self.msg.html(self.message);
            //append to notification container
            self.elem.append(self.close);
            self.elem.append(self.msg);
            self.container.append(self.elem);
            //autoclose after duration
            if( self.duration>0 )
            {
                self.elem.delay(self.duration).slideUp(300, function() {
                    $(this).remove();
                });
            }
        };
        
        //hide notification
        self.hide = function() {
            if( self.elem!==undefined )
                self.elem.remove();
        };
    };

}));
