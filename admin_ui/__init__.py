# -*- coding: utf-8 -*-
"""admin_ui — брендовая админка Wagtail: бирюза, бумага, крупные подписи.

Подключение уже сделано в tochka/settings.py (приложение в INSTALLED_APPS).
Панели редактора — в admin_ui/panels.py, подключены в trips/models.py.
"""

from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks

# Версия в адресе файлов: браузер не должен держать старую тему.
# Меняем число после правки admin.css или admin.js — иначе «ничего не поменялось».
ADMIN_UI_VERSION = 7


@hooks.register("insert_global_admin_css")
def global_admin_css():
    """Тема админки: бирюзовый акцент на бумажном фоне."""
    return format_html(
        '<link rel="stylesheet" href="{}?v={}">',
        static("admin_ui/css/admin.css"),
        ADMIN_UI_VERSION,
    )


@hooks.register("insert_global_admin_js")
def global_admin_js():
    """Светлая тема без оглядки на системную, мелочи UX, подсказки в полях."""
    return format_html(
        '<script src="{}?v={}"></script>',
        static("admin_ui/js/admin.js"),
        ADMIN_UI_VERSION,
    )


@hooks.register("construct_main_menu")
def russian_menu_labels(request, menu_items):
    """Меню без django- и wagtail-терминов.

    Ключи — реальные имена пунктов меню в Wagtail 7.4: пункт страниц
    называется «explorer», а не «pages», как было в старых версиях.
    """
    labels = {
        "explorer": "Туры и страницы",
        "pages": "Туры и страницы",
        "images": "Фотографии",
        "documents": "Документы",
        "snippets": "Справочники",
        "settings": "Настройки и реквизиты",
        "reports": "Отчёты",
    }
    for item in menu_items:
        key = getattr(item, "name", "")
        if key in labels:
            item.label = labels[key]
