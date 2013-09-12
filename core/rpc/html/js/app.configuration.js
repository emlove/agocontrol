/**
 * Model class
 * @returns {configuration}
 */
function configuration() {
    this.hasNavigation = ko.observable(true);

}


$('.tab-nav li > a').click(function() {
        $(".tab-nav li").each(function() {
            $(this).removeClass('active');
        });

        $(this).parent().toggleClass('active');

        this.$el = $('.tabs');
        var index = $(this).parent().index();
        this.$content = this.$el.find(".tab-content");
        this.$nav = $(this).parent().find('li');
        this.$nav.add(this.$content).removeClass("active");
        this.$nav.eq(index).add(this.$content.eq(index)).addClass("active");
});

/**
 * Initalizes the Configuration model
 */
function init_configuration() {
    model = new configuration();

    model.mainTemplate = function() {
	return "configuration";
    }.bind(model);

    model.navigation = function() {
	return "navigation/configuration";
    }.bind(model);

    ko.applyBindings(model);
}
