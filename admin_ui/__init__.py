# -*- coding: utf-8 -*-
"""admin_ui — брендовая админка Wagtail: бирюза, бумага, крупные подписи.

Подключение уже сделано в tochka/settings.py (приложение в INSTALLED_APPS).
Панели редактора — в admin_ui/panels.py, подключены в trips/models.py.
"""

from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks


@hooks.register("insert_global_admin_css")
def global_admin_css():
    """Тема админки: бирюзовый акцент на бумажном фоне."""
    return format_html(
        '<link rel="stylesheet" href="{}">', static("admin_ui/css/admin.css")
    )


@hooks.register("insert_global_admin_js")
def global_admin_js():
    """Мелочи UX: человеческие подсказки в полях тура."""
    return format_html(
        '<script src="{}"></script>', static("admin_ui/js/admin.js")
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
