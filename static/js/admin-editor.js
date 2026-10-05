/*
 * Трёхколоночный экран редактора страницы.
 *
 * Слева  — навигация по панелям, параметры и быстрые действия
 * Центр  — форма (её не трогаем)
 * Справа — живой предпросмотр, кольцо готовности, чек-лист
 *
 * Скрипт ничего не ломает без себя: если разметка не найдена,
 * раскладка остаётся стандартной.
 */
(function () {
  "use strict";

  var EDIT_VIEW = "/cms/pages/";

  function isEditView() {
    return (
      window.location.pathname.indexOf(EDIT_VIEW) !== -1 &&
      !window.location.pathname.includes("/add_subpage") &&
      window.location.pathname.split("/").length > 5
    );
  }

  function pageId() {
    var m = window.location.pathname.match(/\/pages\/(\d+)\//);
    return m ? m[1] : null;
  }

  /* ── Левая колонка ─────────────────────────────────────────── */

  function buildLeftRail(panels) {
    var rail = document.createElement("aside");
    rail.className = "nw-left-rail";

    var heading = document.createElement("div");
    heading.className = "nw-left-rail__title";
    heading.textContent = "На этой странице";
    rail.appendChild(heading);

    panels.forEach(function (panel) {
      var a = document.createElement("a");
      a.href = "#" + panel.id;
      a.textContent = panel.title;
      a.dataset.target = panel.id;
      rail.appendChild(a);
    });

    return rail;
  }

  /* ── Правая колонка ────────────────────────────────────────── */

  function buildRightRail(id) {
    var rail = document.createElement("aside");
    rail.className = "nw-right-rail";

    /* предпросмотр */
    var previewTitle = document.createElement("div");
    previewTitle.className = "nw-right-rail__title";
    previewTitle.textContent = "Предпросмотр";
    rail.appendChild(previewTitle);

    var devices = document.createElement("div");
    devices.className = "nw-devices";
    [
      { key: "desktop", label: "Компьютер" },
      { key: "tablet", label: "Планшет" },
      { key: "phone", label: "Телефон" },
    ].forEach(function (d, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = d.label;
      if (i === 0) b.classList.add("is-active");
      b.addEventListener("click", function () {
        devices.querySelectorAll("button").forEach(function (x) {
          x.classList.remove("is-active");
        });
        b.classList.add("is-active");
        preview.dataset.device = d.key;
      });
      devices.appendChild(b);
    });
    rail.appendChild(devices);

    var preview = document.createElement("div");
    preview.className = "nw-preview";
    preview.dataset.device = "desktop";

    var frame = document.createElement("iframe");
    frame.title = "Предпросмотр страницы";
    frame.src = "/cms/pages/" + id + "/edit/preview/";
    preview.appendChild(frame);
    rail.appendChild(preview);

    var open = document.createElement("button");
    open.type = "button";
    open.className = "nw-rail-actions";
    open.style.cssText = "margin-top:12px;padding:10px 14px;border-radius:10px;" +
      "border:1px solid var(--nw-line-strong);background:var(--nw-surface);cursor:pointer;";
    open.textContent = "Открыть предпросмотр в новой вкладке";
    open.addEventListener("click", function () {
      window.open("/cms/pages/" + id + "/edit/preview/", "_blank", "noopener");
    });
    rail.appendChild(open);

    /* чек-лист */
    var checklistTitle = document.createElement("div");
    checklistTitle.className = "nw-right-rail__title";
    checklistTitle.textContent = "Готовность страницы";
    rail.appendChild(checklistTitle);

    var progress = document.createElement("div");
    progress.className = "nw-progress";
    progress.innerHTML =
      '<div class="nw-progress__ring" data-value="0" style="--value:0"></div>' +
      '<div class="nw-progress__label">Считаем…</div>';
    rail.appendChild(progress);

    var checklist = document.createElement("div");
    checklist.className = "nw-checklist";
    rail.appendChild(checklist);

    /* быстрые действия */
    var actionsTitle = document.createElement("div");
    actionsTitle.className = "nw-right-rail__title";
    actionsTitle.textContent = "Действия";
    rail.appendChild(actionsTitle);

    var actions = document.createElement("div");
    actions.className = "nw-rail-actions";
    actions.innerHTML = [
      ['/cms/schedule/', 'Расписание выездов', 'is-primary'],
      ['/cms/pages/', 'Все страницы', ''],
    ]
      .map(function (row) {
        return (
          '<a class="' + row[2] + '" href="' + row[0] + '">' + row[1] + "</a>"
        );
      })
      .join("");
    rail.appendChild(actions);

    var meta = document.createElement("div");
    meta.className = "nw-meta";
    meta.style.marginTop = "18px";
    meta.textContent =
      "Полоса готовности считает заполненность обязательных полей. " +
      "Клик по пункту подсвечивает нужное поле.";
    rail.appendChild(meta);

    return { rail: rail, frame: frame, progress: progress, checklist: checklist };
  }

  /* ── Чек-лист готовности ───────────────────────────────────── */

  function renderChecklist(percent, items) {
    var ring = this.progress.querySelector(".nw-progress__ring");
    ring.dataset.value = percent;
    ring.style.setProperty("--value", percent);
    ring.dataset.done = percent >= 100 ? "true" : "false";

    this.progress.querySelector(".nw-progress__label").textContent =
      percent >= 100 ? "Готово к публикации" : "Не хватает заполненного";

    this.checklist.innerHTML = "";
    items.forEach(function (item) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "nw-check " + (item.done ? "nw-check--done" : "nw-check--todo");
      b.innerHTML =
        '<span class="nw-check__mark">' + (item.done ? "✓" : "!") + "</span>" +
        "<span>" + item.label + "</span>";

      b.addEventListener("click", function () {
        flashField(item.anchor);
      });
      this.checklist.appendChild(b);
    }, this);
  }

  function flashField(anchor) {
    if (!anchor) return;
    var target = document.querySelector("." + anchor) || document.getElementById(anchor);
    if (!target) return;

    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("nw-field-flash");
    setTimeout(function () {
      target.classList.remove("nw-field-flash");
    }, 2000);
  }

  /* Данные для чек-листа кладём в data-атрибут на body */
  function readChecklist() {
    var node = document.getElementById("nw-checklist-data");
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      return null;
    }
  }

  /* Забираем чек-лист с сервера: он всегда актуален, даже если страницу
     открыли в соседней вкладке и она успела измениться. */
  function fetchChecklist(id, render) {
    fetch("/cms/nw/checklist/" + id + "/", { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data && !data.error) render(data); })
      .catch(function () { /* нет сети — просто не показываем чек-лист */ });
  }

  /* ── Запуск ────────────────────────────────────────────────── */

  function init() {
    if (!isEditView()) return;

    var id = pageId();
    if (!id) return;

    var content = document.getElementById("content") || document.querySelector("#content");
    if (!content) return;

    var panels = [];
    content.querySelectorAll(".w-panel").forEach(function (panel, i) {
      var heading = panel.querySelector(".w-panel__header h2, .w-panel__heading");
      if (!heading) return;
      var pid = "nw-panel-" + i;
      panel.id = pid;
      panels.push({ id: pid, title: heading.textContent.trim() });
    });

    var right = buildRightRail(id);
    var left = buildLeftRail(panels);

    document.body.appendChild(left);
    document.body.appendChild(right.rail);
    document.body.classList.add("nw-three-column", "nw-shift-left");

    /* кнопка для узких экранов */
    var fab = document.createElement("button");
    fab.type = "button";
    fab.className = "nw-preview-fab";
    fab.textContent = "Предпросмотр";
    fab.addEventListener("click", function () {
      right.rail.classList.toggle("is-open");
    });
    document.body.appendChild(fab);

    /* подсветка активного пункта в левой колонке */
    var railLinks = left.querySelectorAll("a");
    var panelsEls = panels.map(function (p) {
      return document.getElementById(p.id);
    });
    railLinks.forEach(function (link, i) {
      link.addEventListener("click", function () {
        railLinks.forEach(function (x) {
          x.classList.remove("is-active");
        });
        link.classList.add("is-active");
      });
    });

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            var idx = panelsEls.indexOf(entry.target);
            if (idx < 0) return;
            railLinks.forEach(function (x) {
              x.classList.remove("is-active");
            });
            if (railLinks[idx]) railLinks[idx].classList.add("is-active");
          });
        },
        { rootMargin: "-30% 0px -60% 0px" }
      );
      panelsEls.forEach(function (el) {
        if (el) io.observe(el);
      });
    }

    /* чек-лист: сначала то, что уже в разметке, затем свежие данные */
    var data = readChecklist();
    if (data) {
      renderChecklist.call(right, data.percent, data.items);
    }
    fetchChecklist(id, function (fresh) {
      renderChecklist.call(right, fresh.percent, fresh.items);
    });

    /* обновляем предпросмотр после сохранения страницы */
    var refresh = function () {
      right.frame.contentWindow.location.reload();
    };
    if (window.wagtail && wagtail.admin) {
      document.addEventListener("wagtail:save", function () {
        setTimeout(refresh, 900);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();