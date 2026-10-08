/* «Нескучные выходные» — интерактив без зависимостей */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- мобильное меню ---------- */
  var burger = document.querySelector(".burger");
  var nav = document.querySelector(".main-nav");
  if (burger && nav) {
    burger.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") { nav.classList.remove("open"); burger.setAttribute("aria-expanded", "false"); }
    });
  }

  /* ---------- карусель выездов ---------- */
  var scroller = document.querySelector(".trip-scroller");
  if (scroller) {
    var cards = Array.prototype.slice.call(scroller.children);
    var prev = document.querySelector("[data-car='prev']");
    var next = document.querySelector("[data-car='next']");
    var dotsBox = document.querySelector(".car-dots");
    var counter = document.querySelector(".car-counter");
    var idx = 0;

    cards.forEach(function (_, i) {
      if (!dotsBox) { return; }
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", "Выезд " + (i + 1));
      b.addEventListener("click", function () { go(i, true); });
      dotsBox.appendChild(b);
    });
    var dots = dotsBox ? Array.prototype.slice.call(dotsBox.children) : [];

    function go(i, smooth) {
      idx = Math.max(0, Math.min(cards.length - 1, i));
      if (smooth && !reduced) suppressUntil = Date.now() + 900;
      cards[idx].scrollIntoView({ behavior: smooth && !reduced ? "smooth" : "auto", inline: "start", block: "nearest" });
      paint();
    }
    function paint() {
      dots.forEach(function (d, i) { d.setAttribute("aria-current", i === idx ? "true" : "false"); });
      if (counter) counter.textContent = (idx + 1) + " из " + cards.length;
      if (prev) prev.disabled = idx === 0;
      if (next) next.disabled = idx === cards.length - 1;
    }
    var suppressUntil = 0;
    if ("onscrollend" in window) {
      scroller.addEventListener("scrollend", function () { suppressUntil = 0; });
    }
    var tick = false;
    scroller.addEventListener("scroll", function () {
      if (tick || Date.now() < suppressUntil) return;
      tick = true;
      requestAnimationFrame(function () {
        var x = scroller.scrollLeft + 40;
        var best = 0, bd = 1e9;
        cards.forEach(function (c, i) {
          var d = Math.abs(c.offsetLeft - x);
          if (d < bd) { bd = d; best = i; }
        });
        idx = best; paint(); tick = false;
      });
    });
    if (prev) prev.addEventListener("click", function () { go(idx - 1, true); });
    if (next) next.addEventListener("click", function () { go(idx + 1, true); });
    paint();
  }

  /* ---------- аккордеон FAQ ---------- */
  document.querySelectorAll(".acc-item").forEach(function (item) {
    var btn = item.querySelector(".acc-btn");
    var panel = item.querySelector(".acc-panel");
    btn.addEventListener("click", function () {
      var open = item.classList.contains("open");
      item.closest(".acc").querySelectorAll(".acc-item.open").forEach(function (o) {
        o.classList.remove("open");
        o.querySelector(".acc-panel").style.maxHeight = "0px";
        o.querySelector(".acc-btn").setAttribute("aria-expanded", "false");
      });
      if (!open) {
        item.classList.add("open");
        panel.style.maxHeight = panel.scrollHeight + "px";
        btn.setAttribute("aria-expanded", "true");
      }
    });
    /* фото в программе дня догружаются после клика — иначе панель обрежет их */
    panel.querySelectorAll("img").forEach(function (img) {
      if (img.complete) return;
      img.addEventListener("load", function () {
        if (item.classList.contains("open")) panel.style.maxHeight = panel.scrollHeight + "px";
      });
    });
  });
  var first = document.querySelector(".acc-item .acc-btn");
  if (first) first.click();

  /* ---------- hero-галерея тура ---------- */
  var heroBox = document.querySelector("[data-hero]");
  if (heroBox) {
    var slides = Array.prototype.slice.call(heroBox.querySelectorAll("[data-slide]"));
    var thumbs = Array.prototype.slice.call(heroBox.querySelectorAll("[data-thumb]"));
    var cur = 0, timer = null;
    var setSlide = function (i) {
      cur = i;
      slides.forEach(function (s, k) { s.classList.toggle("on", k === i); });
      thumbs.forEach(function (t, k) { t.classList.toggle("on", k === i); });
    };
    var auto = function () {
      if (reduced || slides.length < 2) return;
      clearInterval(timer);
      timer = setInterval(function () { setSlide((cur + 1) % slides.length); }, 6000);
    };
    thumbs.forEach(function (t, k) {
      t.addEventListener("click", function () { setSlide(k); auto(); });
    });
    setSlide(0); auto();
  }

  /* ---------- выбор заезда на странице тура ---------- */
  var dbox = document.querySelector("[data-dates]");
  if (dbox) {
    var dcards = Array.prototype.slice.call(dbox.querySelectorAll(".date-row[data-label]"));
    var sLine = document.getElementById("selLine");
    var sA = document.getElementById("selLink");
    var tourName = dbox.dataset.tour || "";
    var pick = function (i) {
      dcards.forEach(function (c, k) { c.classList.toggle("sel", k === i); });
      var c = dcards[i];
      if (!c || !sLine) return;
      var spots = Number(c.dataset.spots);
      sLine.textContent = c.dataset.label + " · " + c.dataset.price + " · " + (spots > 0 ? spots + " своб. мест" : "лист ожидания");
      if (sA) {
        var base = sA.getAttribute("data-chat-base") || "";
        if (base.indexOf("t.me") > -1) {
          var sep = base.indexOf("?") > -1 ? "&" : "?";
          sA.href = base + sep + "tour=" + encodeURIComponent(tourName) +
            "&date=" + encodeURIComponent(c.dataset.label);
        }
      }
    };
    dcards.forEach(function (c, k) { c.addEventListener("click", function () { pick(k); }); });
    if (dcards.length) pick(0);
  }

  /* ---------- куки-баннер ---------- */
  // Согласие ставит сервер на /cookie-accept/, но делать это надо молча:
  // обычный переход перезагружал страницу и выбрасывал наверх.
  var cookieBar = document.getElementById("cookieBar");
  var cookieOk = document.getElementById("cookieOk");
  if (cookieBar && cookieOk) {
    cookieOk.addEventListener("click", function (e) {
      e.preventDefault();
      var url = cookieOk.getAttribute("href");
      fetch(url, { credentials: "same-origin" })
        .then(function () { cookieBar.remove(); })
        .catch(function () { window.location.href = url; });
    });
  }

  /* ---------- всплывающие мессенджеры ---------- */
  var fab = document.getElementById("mwFab");
  var panel = document.getElementById("mwPanel");
  if (fab && panel) {
    fab.addEventListener("click", function () {
      panel.classList.add("open"); fab.classList.add("hide");
    });
    document.getElementById("mwClose").addEventListener("click", function () {
      panel.classList.remove("open"); fab.classList.remove("hide");
    });
  }

  /* ---------- фильтры каталога ---------- */
  var grid = document.querySelector("[data-catalog]");
  if (grid) {
    var cardsAll = Array.prototype.slice.call(grid.children);
    var chips = Array.prototype.slice.call(document.querySelectorAll("[data-filter-type]"));
    var selDur = document.querySelector("[data-filter-duration]");
    var selDist = document.querySelector("[data-filter-distance]");
    var selDate = document.querySelector("[data-filter-date]");
    var count = document.querySelector("[data-count]");
    var state = { type: "all", dur: "all", dist: "all", date: "all" };

    function apply() {
      var shown = 0;
      cardsAll.forEach(function (c) {
        var okType = state.type === "all" || c.dataset.type === state.type;
        var okDur = state.dur === "all" || c.dataset.duration === state.dur;
        var okDist = state.dist === "all" ||
          (c.dataset.distance ? c.dataset.distance === state.dist : c.dataset.spots === state.dist);
        var okDate = state.date === "all" ||
          (c.dataset.daysAway ? Number(c.dataset.daysAway) <= Number(state.date)
                              : (c.dataset.months || "").split(",").indexOf(state.date) !== -1);
        var ok = okType && okDur && okDist && okDate;
        c.style.display = ok ? "" : "none";
        if (ok) shown++;
      });
      if (count) count.textContent = shown + " " + plural(shown, "направление", "направления", "направлений");
    }
    function plural(n, a, b, c) {
      var m = n % 100; if (m >= 11 && m <= 14) return c;
      m = n % 10; return m === 1 ? a : m >= 2 && m <= 4 ? b : c;
    }
    chips.forEach(function (ch) {
      ch.addEventListener("click", function () {
        chips.forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
        ch.setAttribute("aria-pressed", "true");
        state.type = ch.dataset.filterType;
        apply();
      });
    });
    [[selDur, "dur"], [selDist, "dist"], [selDate, "date"]].forEach(function (p) {
      if (p[0]) p[0].addEventListener("change", function () { state[p[1]] = p[0].value; apply(); });
    });
    apply();
  }

  /* ---------- появление секций ---------- */
  if (!reduced && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: .12 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
  }
})();
