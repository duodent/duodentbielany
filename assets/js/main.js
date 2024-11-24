/* ============================
Template Name  : Dentax
Description    : Dentist & Dental Clinic HTML5 Template
Author         : Youtoview
Version        : 1.1
=============================== */


jQuery(
    (function ($) {
        "use strict";

        //sticky nav
        $(window).on("scroll", function () {
            if ($(this).scrollTop() > 120) {
                $(".navbar-area").addClass("is-sticky");
            } else {
                $(".navbar-area").removeClass("is-sticky");
            }
        });


        // mean menu
        jQuery(".mean-menu").meanmenu({ meanScreenWidth: "991" });

        // counter up	   
        $('.counter').counterUp({
            delay: 10,
            time: 5000
        });

        // home slider
        $(".home-slides").owlCarousel({ loop: true, nav: true, dots: false, autoplayHoverPause: false, autoplay: false, items: 1, navText: ["<i class='flaticon-left-arrow-1'></i>", "<i class='flaticon-next'></i>"] });
        $(".home-slides").on("translate.owl.carousel", function () {
            $(".main-slides-content .sub-title").removeClass("animated fadeInDown").css("opacity", "0");
            $(".main-slides-content h1").removeClass("animated fadeInUp").css("opacity", "0");
            $(".main-slides-content p").removeClass("animated fadeInUp").css("opacity", "0");
            $(".main-slides-content .slides-btn .default-btn").removeClass("animated fadeInUp").css("opacity", "0");
            $(".main-slides-content .slides-btn .optional-btn").removeClass("animated fadeInUp").css("opacity", "0");
            $(".main-slides-content .slides-btn .checkup-content").removeClass("animated fadeInUp").css("opacity", "0");
        });
        $(".home-slides").on("translated.owl.carousel", function () {
            $(".main-slides-content .sub-title").addClass("animated fadeInDown").css("opacity", "1");
            $(".main-slides-content h1").addClass("animated fadeInUp").css("opacity", "1");
            $(".main-slides-content p").addClass("animated fadeInUp").css("opacity", "1");
            $(".main-slides-content .slides-btn .default-btn").addClass("animated fadeInUp").css("opacity", "1");
            $(".main-slides-content .slides-btn .optional-btn").addClass("animated fadeInUp").css("opacity", "1");
            $(".main-slides-content .slides-btn .checkup-content").addClass("animated fadeInUp").css("opacity", "1");
        });

        // review slider
        $(".review-slides").owlCarousel({ loop: true, nav: false, dots: true, autoplayHoverPause: true, autoplay: false, margin: 30, responsive: { 0: { items: 1 }, 768: { items: 2 }, 1200: { items: 2 } } });

        // client slider
        $(".client-slides").owlCarousel({ loop: true, nav: false, dots: false, autoplayHoverPause: true, autoplay: true, margin: 30, responsive: { 0: { items: 2 }, 768: { items: 3 }, 1200: { items: 6 } } });

        // tab
        $(".tab ul.tabs").addClass("active").find("> li:eq(0)").addClass("current");
        $(".tab ul.tabs li a").on("click", function (g) {
            var tab = $(this).closest(".tab"),
                index = $(this).closest("li").index();
            tab.find("ul.tabs > li").removeClass("current");
            $(this).closest("li").addClass("current");
            tab.find(".tab_content")
                .find("div.tabs_item")
                .not("div.tabs_item:eq(" + index + ")")
                .slideUp();
            tab.find(".tab_content")
                .find("div.tabs_item:eq(" + index + ")")
                .slideDown();
            g.preventDefault();
        });

        // accordion
        $(".accordion")
            .find(".accordion-title")
            .on("click", function () {
                $(this).toggleClass("active");
                $(this).next().slideToggle("fast");
                $(".accordion-content").not($(this).next()).slideUp("fast");
                $(".accordion-title").not($(this)).removeClass("active");
            });


        //countdown
        function makeTimer() {
            var endTime = new Date("December 13, 2030 18:00:00 PDT");
            var endTime = Date.parse(endTime) / 1000;
            var now = new Date();
            var now = Date.parse(now) / 1000;
            var timeLeft = endTime - now;
            var days = Math.floor(timeLeft / 86400);
            var hours = Math.floor((timeLeft - days * 86400) / 3600);
            var minutes = Math.floor((timeLeft - days * 86400 - hours * 3600) / 60);
            var seconds = Math.floor(timeLeft - days * 86400 - hours * 3600 - minutes * 60);
            if (hours < "10") {
                hours = "0" + hours;
            }
            if (minutes < "10") {
                minutes = "0" + minutes;
            }
            if (seconds < "10") {
                seconds = "0" + seconds;
            }
            $("#days").html(days + "<span>Days</span>");
            $("#hours").html(hours + "<span>Hours</span>");
            $("#minutes").html(minutes + "<span>Minutes</span>");
            $("#seconds").html(seconds + "<span>Seconds</span>");
        }
        setInterval(function () {
            makeTimer();
        }, 0);


        // nice select
        $("select").niceSelect();

        // magnific Popup
        $(".popup-youtube").magnificPopup({ disableOn: 320, type: "iframe", mainClass: "mfp-fade", removalDelay: 160, preloader: false, fixedContentPos: false });


        // go top
        $(window).on("scroll", function () {
            var scrolled = $(window).scrollTop();
            if (scrolled > 600) $(".go-top").addClass("active");
            if (scrolled < 600) $(".go-top").removeClass("active");
        });

        $(".go-top").on("click", function () {
            $("html, body").animate({ scrollTop: "0" }, 500);
        });


        // wow js
        $(window).on("load", function () {
            if ($(".wow").length) {
                var wow = new WOW({ boxClass: "wow", animateClass: "animated", offset: 20, mobile: true, live: true });
                wow.init();
            }
        });


        // copyright date
        var date = new Date().getFullYear();
        $('#date').html(date);


        // preloader
        $(window).on("load", function () {
            $(".preloader").fadeOut();
        });


    })(jQuery)
);
