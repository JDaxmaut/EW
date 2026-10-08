/* Админка «Нескучные выходные»: мелкие правки интерфейса.
 *
 * 0) Тема только светлая. Wagtail вешает на <body> класс w-theme-system
 *    и, если у человека в системе тёмная тема, меняет токены на светлый
 *    текст. Наша тема при этом оставляет фон светлым, и получается
 *    светлый текст на светлом фоне — буквы пропадают. Поэтому класс
 *    темы заменяем на w-theme-light.
 * 1) Примеры-подсказки в пустых полях тура.
 * 2) Убираем черновики: Wagtail рисует «Сохранить черновик» и «Опубликовать».
 *    Оставляем одну кнопку «Сохранить», которая публикует страницу
 *    (сама публикация обеспечена в trips/publish_always.py).
 * 3) Прячем «Посмотреть историю» — версии нужны для отката, но в меню они
 *    только мешают.
 */
(function () {
  "use strict";

  /* Тема админки: всегда светлая, независимо от настроек системы.
     У Wagtail только два класса темы — w-theme-system и w-theme-dark;
     оба включают тёмные токены. Если убрать их, остаются базовые
     светлые значения из :root, и «системная» тема перестаёт мешать. */
  function forceLightTheme() {
    [document.documentElement, document.body].forEach(function (node) {
      if (!node || !node.classList) return;
      node.classList.remove("w-theme-system");
      node.classList.remove("w-theme-dark");
    });
  }

  function setFieldExamples() {
    var examples = {
      summary: "Например: Дикий песок между скалами, 2,5 ч в пути",
      price_from: "Например: 1 900",
      subtitle: "Например: Дикий пляж в сосновом бору",
      travel_time: "Например: 2,5 ч",
      parking: "Например: платная, 300 ₽/день",
    };
    Object.keys(examples).forEach(function (field) {
      var el = document.getElementById("id_" + field);
      if (el && !el.placeholder) el.placeholder = examples[field];
    });
  }

  /* Кнопка «Сохранить черновик»: убираем совсем, чтобы нельзя было
     случайно оставить страницу неопубликованной. */
  function dropDraftButton() {
    document
      .querySelectorAll("button.action-save, .action-save .icon-draft")
      .forEach(function (el) {
        var btn = el.closest("button") || el;
        if (btn && btn.parentNode) btn.parentNode.removeChild(btn);
      });
  }

  /* «Опубликовать» → «Сохранить»: редактору не нужно слово «публикация»,
     он просто сохраняет правку и сразу видит её на сайте.
     Кнопка публикации у Wagtail 7.4 опознаётся по name="action-publish",
     а не по классу, поэтому ищем оба признака. */
  function renamePublishButton() {
    document
      .querySelectorAll('button[name="action-publish"], button.action-publish')
      .forEach(function (btn) {
        var label =
          btn.querySelector("em") ||
          [...btn.childNodes].find(function (n) {
            return n.nodeType === 3 && n.textContent.trim();
          });
        if (label && /Опубликовать|опубликовать|Publish/i.test(label.textContent)) {
          label.textContent = "Сохранить";
          btn.setAttribute("title", "Сохранить и сразу показать на сайте");
        }
      });
  }

  function dropHistoryLink() {
    document
      .querySelectorAll("a, button")
      .forEach(function (el) {
        if (/посмотреть историю/i.test(el.textContent || "") && el.children.length === 0) {
          if (el.parentNode) el.parentNode.removeChild(el);
        }
      });
  }

  /* Меню «Больше действий» с пустым смыслом убираем: черновиков и снятия
     с публикации у нас нет, история скрыта, остаётся пустое меню. */
  function dropEmptyActionMenu() {
    document.querySelectorAll(".w-dropdown").forEach(function (dd) {
      var menu = dd.querySelector(".w-dropdown__menu");
      if (menu && !menu.textContent.trim()) {
        if (dd.parentNode) dd.parentNode.removeChild(dd);
      }
    });
  }

  function run() {
    forceLightTheme();
    setFieldExamples();
    dropDraftButton();
    renamePublishButton();
    dropHistoryLink();
    dropEmptyActionMenu();
  }

  function boot() {
    run();
    /* Редактор в Wagtail 7 частично перерисовывается React'ом, поэтому
       повторяем правки, когда появляются новые узлы. */
    if (window.MutationObserver) {
      var pending = false;
      new MutationObserver(function () {
        if (pending) return;
        pending = true;
        window.requestAnimationFrame(function () {
          pending = false;
          run();
        });
      }).observe(document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
