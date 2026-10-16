// Loads Google Analytics only after the visitor clicks Accept.
// The choice is kept in localStorage under "analytics-consent".
(function () {
  var STORAGE_KEY = "analytics-consent";
  var GA_ID = "G-SE674YJENK";
  var GA_COOKIES = ["_ga", "_ga_" + GA_ID.slice(2)];
  var loaded = false;

  function readChoice() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return null;
    }
  }

  function saveChoice(choice) {
    try {
      window.localStorage.setItem(STORAGE_KEY, choice);
    } catch (error) {
      // Storage blocked: the choice applies to this page only.
    }
  }

  function loadAnalytics() {
    window["ga-disable-" + GA_ID] = false;
    if (loaded) {
      return;
    }
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () {
      window.dataLayer.push(arguments);
    };
    window.gtag("js", new Date());
    window.gtag("config", GA_ID);
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
    document.head.appendChild(script);
  }

  function stopAnalytics() {
    // Google's documented switch: gtag sends nothing more from this page.
    window["ga-disable-" + GA_ID] = true;
    var host = window.location.hostname;
    var domains = ["", host, "." + host];
    GA_COOKIES.forEach(function (name) {
      domains.forEach(function (domain) {
        document.cookie =
          name +
          "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" +
          (domain ? "; domain=" + domain : "");
      });
    });
  }

  function init() {
    var banner = document.getElementById("consent-banner");
    if (!banner) {
      return;
    }

    banner.addEventListener("click", function (event) {
      var choice = event.target.getAttribute("data-consent");
      if (!choice) {
        return;
      }
      saveChoice(choice);
      if (choice === "accepted") {
        loadAnalytics();
      } else {
        stopAnalytics();
      }
      banner.hidden = true;
    });

    document.querySelectorAll("[data-cookie-settings]").forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        banner.hidden = false;
        banner.querySelector("button").focus();
      });
    });

    var choice = readChoice();
    if (choice === "accepted") {
      loadAnalytics();
    } else if (choice === "declined") {
      stopAnalytics();
    } else {
      banner.hidden = false;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
