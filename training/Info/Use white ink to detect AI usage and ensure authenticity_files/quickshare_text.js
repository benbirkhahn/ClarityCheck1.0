var pp_quickshare = (function($) {

    var shareUrl = window.location.href;

    var init = function(shorturl) {

        if (shorturl) {
            shareUrl = shorturl;
        }

        bindUIActions();

    };

    var bindUIActions = function() {
        var releaseId = '';
        $(document).mousedown(function(e) {
            checkTarget(e);
        });
        $('.content_main_case').mouseup(function(e) {
            if ($('.pp_quickshare_tools').length) {
                return;
            }
            releaseId = $(this).data('release-id');
            show_quickshare(e);
        });
        $('.pp-bodywrapper').on('click', '.pp_quickshare_twitter', function() {
            sharePopups.twitter();
            TrackVisits.resourceClicked('sharepagex', releaseId);
            removeQuickshare();
        });
        // $('.pp-bodywrapper').on('click', '.pp_quickshare_facebook', function() {
        //     sharePopups.facebook();
        //     removeQuickshare();
        // });
        $('.pp-bodywrapper').on('click', '.pp_quickshare_linkedin', function() {
            sharePopups.linkedin();
            TrackVisits.resourceClicked('sharepagelinkedin', releaseId);
            removeQuickshare();
        });
    };

    var getRawMsg = function() {
        var markedContent_raw = "";

        if (window.getSelection) {
            markedContent_raw = window.getSelection().toString();
        } else if (document.selection && document.selection.type != "Control") {
            markedContent_raw = document.selection.createRange().text;
        }

        markedContent_raw = markedContent_raw.replace(/(\r\n|\n|\r)/g, '');
        markedContent_raw = markedContent_raw.replace(/\s+/g, ' ');

        return markedContent_raw;
    };

    var getMsg = function(rawMessage) {
        var markedContent = encodeURIComponent($.trim(rawMessage.toString()));
        markedContent = markedContent.replace('undefined', '');
        markedContent = markedContent.replace(/'/g, "\\'");

        return markedContent;
    };

    var sharePopups = {

        twitter: function() {
            msg = $('.pp_quickshare_textarea').val();
            var url = '//x.com/intent/post?text=' + msg;
            var title = '';
            var width = 650;
            var height = 500;
            var left = screen.width / 2 - width / 2;
            var top = screen.height / 2 - height / 2 - 100;
            return window.open(url, title, 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=' + width + ', height=' + height + ', top=' + top + ', left=' + left);
        },

        linkedin: function() {
            msg = $('.pp_quickshare_textarea').val();
            msg = encodeURIComponent(msg);
            var url = "https://www.linkedin.com/shareArticle?mini=true&url=" + shareUrl + "&title=" + msg + "";
            var width = 640;
            var height = 440;
            var left = screen.width / 2 - width / 2;
            var top = screen.height / 2 - height / 2 - 100;
            return window.open(url, "share_linkedin", "toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=" + width + ", height=" + height + ", top=" + top + ", left=" + left)
        }

    };

    var removeQuickshare = function() {
        $(".pp_quickshare_tools").remove();
    };

    var checkTarget = function(e) {
        var container = $(".pp_quickshare_tools");
        if (!container.is(e.target) // if the target of the click isn't the container...
            && container.has(e.target).length === 0) // ... nor a descendant of the container
        {
            removeQuickshare();
        }
    };

    var show_quickshare = function(e) {

        var windowWidth = $(window).width();
        var quickshareWidth = 460;
        var quickshareStyle = "";
        var clientXpos = "";
        var clientXpos = "";
        var qs_right = 0;

        if (window.event) {
            clientXpos = window.event.clientX;
            clientYpos = window.event.clientY;
        } else {
            clientXpos = e.clientX;
            clientYpos = e.clientY;
        }

        scrollYpos = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;

        var qs_left = clientXpos + document.body.scrollLeft + 10;
        var qs_top = clientYpos + scrollYpos + 10;
        if (qs_left + quickshareWidth > windowWidth) {
            quickshareStyle = 'style="right: ' + qs_right + 'px;top:' + qs_top + 'px"';
        } else {
            quickshareStyle = 'style="left: ' + qs_left + 'px;top:' + qs_top + 'px"';
        }

        var markedContent_raw = getRawMsg();
        var msg = getMsg(markedContent_raw);

        var tpl = '<div class="pp_quickshare_tools" ' + quickshareStyle + '>' +
            '<div class="pp_quickshare_triangle"></div>' +
            '<textarea class="pp_quickshare_textarea">' + markedContent_raw + " " + shareUrl + '</textarea>' +
            '<div class="pp_quickshare_items">' +
            '<div class="pp_quickshare_item pp_quickshare_twitter">' +
            '<span class="pp_quickshare_text">Post</span>' +
            '<span class="pp_quickshare_icon pp_icon pp_icon_twitter"></span>' +
            '</div>' +
            // '<div class="pp_quickshare_item pp_quickshare_facebook">' +
            // '<span class="pp_quickshare_text">Share</span>' +
            // '<span class="pp_quickshare_icon pp_icon pp_icon_facebook2"></span>' +
            // '</div>' +
            '<div class="pp_quickshare_item pp_quickshare_linkedin">' +
            '<span class="pp_quickshare_text">Share</span>' +
            '<span class="pp_quickshare_icon pp_icon pp_icon_linkedin"></span>' +
            '</div>' +
            '</div>' +
            '</div>';

        var marked_length = markedContent_raw.length;

        if (marked_length > 25) {
            $(".pp-bodywrapper").append(tpl);
            $(".pp_quickshare_tools").slideDown(80);
        }
    };

    return {

        init: init

    }
})(pp_jquery);
