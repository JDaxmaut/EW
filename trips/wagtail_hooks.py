"""
Кастомизация админки Wagtail под обычного человека.

Что делает этот файл:
  1. Подключает свой CSS (палитра «Нескучные выходные» + трёхколоночный экран).
  2. Добавляет на главную админки панели: быстрые действия, черновики, ближайшие выезды.
  3. Добавляет пункт меню «Расписание выездов» с быстрым редактированием цен и мест.
  4. Показывает в правой колонке редактора живой предпросмотр и чек-лист готовности.
"""

import json
from datetime import date, timedelta

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.ui.components import Component
from wagtail.admin.widgets import PageListingButton

CSS_VERSION = "v5"


# ─────────────────────────── Стили и скрипты ───────────────────────────
# Стили админки живут в admin_ui/static/admin_ui/css/admin.css: туда же
# переехали стили чек-листа, панелей и превью, раньше бывшие здесь.
# Вторую ссылку на тему подключать нельзя — она грузилась последней и
# перебивала ту, что ниже, отсюда был «сливающийся» текст.


@hooks.register("insert_global_admin_js")
def admin_custom_js():
    return format_html(
        '<script src="{}?{}" defer></script>',
        static("js/admin-editor.js"),
        CSS_VERSION,
    )


# ─────────────────────────── Панели дашборда ───────────────────────────

class QuickActionsPanel(Component):
    name = "quick_actions"
    order = 40

    def __init__(self, request=None):
        self.request = request

    def render_html(self, parent_context=None):
        # request обязателен: без него {% csrf_token %} в формах панелей
        # получает пустую строку и сохранение падает с 403.
        return mark_safe(
            render_to_string("wagtailadmin/panels/quick_actions.html", {}, request=self.request)
        )


class IncompleteDestinationsPanel(Component):
    name = "incomplete_destinations"
    order = 51

    def __init__(self, request=None):
        self.request = request

    def render_html(self, parent_context=None):
        from trips.models import Destination

        rows = []
        for dest in Destination.objects.live().order_by("title"):
            percent = dest.completeness_percent()
            if percent < 100:
                missing = [i["label"] for i in dest.completeness_items() if not i["done"]]
                rows.append({"page": dest, "percent": percent, "missing": missing})
        if not rows:
            return mark_safe("")
        return mark_safe(
            render_to_string(
                "wagtailadmin/panels/incomplete_destinations.html",
                {"rows": rows},
                request=self.request,
            )
        )


class UpcomingDeparturesPanel(Component):
    name = "upcoming_departures"
    order = 52

    def __init__(self, request=None):
        self.request = request

    def render_html(self, parent_context=None):
        from trips.models import Departure

        departures = (
            Departure.objects.upcoming()
            .select_related("destination")
            .order_by("start_date")[:20]
        )
        return mark_safe(
            render_to_string(
                "wagtailadmin/panels/upcoming_departures.html",
                {"departures": departures},
                request=self.request,
            )
        )


@hooks.register("construct_homepage_panels")
def customize_homepage_panels(request, panels):
    keep = {"site_summary"}
    panels[:] = [p for p in panels if getattr(p, "name", None) in keep]
    panels.insert(0, QuickActionsPanel(request))
    panels.insert(1, UpcomingDeparturesPanel(request))
    panels.append(IncompleteDestinationsPanel(request))
    # Панели черновиков нет: сохранение всегда публикует страницу, поэтому
    # «черновики» в админке не появляются вовсе.


# ─────────────────── Экран расписания выездов ───────────────────

def schedule_view(request):
    from trips.models import Departure, Destination

    today = date.today()
    departures = (
        Departure.objects.select_related("destination")
        .filter(start_date__gte=today - timedelta(days=30))
        .order_by("start_date")
    )
    destinations = Destination.objects.live().order_by("title")
    return render(
        request,
        "wagtailadmin/schedule.html",
        {"departures": departures, "destinations": destinations},
    )


@require_POST
def quick_save_departures(request):
    from trips.models import Departure

    changed = 0
    for dep in Departure.objects.select_related("destination"):
        price_key = f"price_{dep.pk}"
        seats_key = f"seats_{dep.pk}"
        dirty = False
        if price_key in request.POST:
            try:
                dep.price = max(1, int(request.POST[price_key]))
                dirty = True
            except ValueError:
                pass
        if seats_key in request.POST:
            try:
                dep.seats_left = max(0, min(int(request.POST[seats_key]), dep.seats_total))
                dirty = True
            except ValueError:
                pass
        if dirty:
            dep.save()
            changed += 1

    request.session["schedule_saved"] = changed
    return HttpResponseRedirect("/cms/schedule/")


def checklist_api(request, page_id):
    """Чек-лист готовности для правой колонки.

    Отдельный эндпоинт надёжнее, чем передача данных через меню:
    JS сам забирает JSON и не зависит от того, как Wagtail собрал разметку.
    """
    from trips.models import Destination

    page = Destination.objects.filter(pk=page_id).first()
    if page is None or not request.user.has_perm("trips.change_destination"):
        return JsonResponse({"error": "Нет доступа"}, status=403)

    return JsonResponse({
        "percent": page.completeness_percent(),
        "items": page.completeness_items(),
    })


# ─────────────────── Список туров ───────────────────

def tours_list_view(request):
    """Все туры сразу, с фото, ценой и готовностью.

    В дереве страниц туры спрятаны под каталогом, и найти нужный
    неудобно. Здесь редактор видит их одним списком и может отфильтровать.
    """
    from trips.models import Destination, DestinationIndexPage

    tours = Destination.objects.select_related("cover").order_by("title")

    query = (request.GET.get("q") or "").strip()
    if query:
        tours = tours.filter(title__icontains=query)

    format_filter = request.GET.get("format") or ""
    if format_filter:
        tours = tours.filter(format=format_filter)

    state = request.GET.get("state") or ""
    if state == "no_cover":
        tours = tours.filter(cover__isnull=True)
    elif state == "ready":
        tours = [t for t in tours if t.completeness_percent() >= 80]
    elif state == "drafts":
        tours = [t for t in tours if t.completeness_percent() < 80]

    catalog = DestinationIndexPage.objects.first()
    return render(
        request,
        "wagtailadmin/tours_list.html",
        {
            "tours": tours,
            "catalog_id": catalog.id if catalog else None,
            "query": query,
            "format_filter": format_filter,
            "state_filter": state,
        },
    )


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("schedule/", schedule_view, name="schedule"),
        path("schedule/quick-save/", quick_save_departures, name="quick_save_departures"),
        path("nw/checklist/<int:page_id>/", checklist_api, name="nw_checklist"),
        path("tours/", tours_list_view, name="tours_list"),
    ]


@hooks.register("register_admin_menu_item")
def register_schedule_menu_item():
    return MenuItem(
        "Расписание выездов",
        "/cms/schedule/",
        icon_name="date",
        order=180,
    )


@hooks.register("register_admin_menu_item")
def register_tours_menu_item():
    """Пункт «Туры» — самый верхний: он нужнее всего редактору."""
    return MenuItem(
        "Туры",
        "/cms/tours/",
        icon_name="site",
        order=100,
    )


# ─────────────────── Данные для правой колонки ───────────────────

class ChecklistData(Component):
    """Кладём чек-лист готовности прямо в HTML редактора.

    В Wagtail 7 хука insert_editor_js больше нет, поэтому данные
    передаём через construct_page_action_menu — он тоже рендерится
    на экране редактирования.
    """

    name = "nw_checklist_data"
    order = 99
    is_shown = True

    def __init__(self, payload):
        self.payload = payload

    def render_html(self, parent_context=None):
        if not self.payload:
            return mark_safe("")
        return format_html(
            '<script id="nw-checklist-data" type="application/json">{}</script>',
            json.dumps(self.payload, ensure_ascii=False),
        )


@hooks.register("construct_page_action_menu")
def add_checklist_to_action_menu(menu_items, request, context):
    """Убираем из меню то, что редактору не нужно, и оставляем чек-лист.

    Хук получает список пунктов меню и дополняет его. Важно: хук не
    генератор — он именно дополняет переданный список, иначе данные
    в разметку не попадут.

    ВАЖНО про action-publish: в Wagtail 7.4 кнопка «Опубликовать» — это
    и есть пункт меню с именем action-publish, и именно она сохраняет
    страницу. Шаблон pages/edit.html выводит {% block actions %} целиком
    из action_menu, поэтому если убрать этот пункт, кнопок сохранения
    не останется вообще. Переименовать её в «Сохранить» делает JS.

    Удаляем: «Сохранить черновик», «Снять с публикации» и пункты workflow
    (модерация выключена). «Посмотреть историю» убирает JS: это не пункт
    меню.
    """
    junk = {
        "action-unpublish",
        "action-cancel-workflow",
        "action-restart-workflow",
        "action-submit-moderation",
    }

    # Кнопку «Сохранить черновик» убираем только тем, кто может публиковать:
    # у такого редактора есть «Опубликовать», а у того, кому публикация
    # запрещена, она остаётся единственным способом сохранить правку.
    page = context.get("page") if isinstance(context, dict) else getattr(context, "page", None)
    user = getattr(request, "user", None)
    can_publish = bool(
        page is not None
        and user is not None
        and user.has_perm("wagtailadmin.change_pagerevision")
        and page.permissions_for_user(user).can_publish()
    )
    if can_publish:
        junk = junk | {"action-save-draft"}

    menu_items[:] = [item for item in menu_items if getattr(item, "name", None) not in junk]

    from trips.models import Destination

    page = context.get("page") if isinstance(context, dict) else getattr(context, "page", None)
    if not isinstance(page, Destination):
        return

    payload = {
        "percent": page.completeness_percent(),
        "items": page.completeness_items(),
    }
    menu_items.append(ChecklistData(payload))


# ─────────────────── Кнопки в списках страниц ───────────────────

@hooks.register("construct_page_listing_buttons")
def add_open_button(buttons, page, user, context=None):
    from trips.models import Destination

    if isinstance(page, Destination) and page.live:
        buttons.append(
            PageListingButton(
                "Открыть",
                page.url,
                attrs={"target": "_blank", "rel": "noopener"},
                priority=20,
            )
        )


# ─────────────────── Чистка лишнего меню ───────────────────

@hooks.register("construct_main_menu")
def hide_menu_items(request, menu_items):
    remove = {"help", "reports"}
    menu_items[:] = [i for i in menu_items if i.name not in remove]


@hooks.register("construct_settings_menu")
def hide_settings_items(request, menu_items):
    remove = {"workflows", "workflow-tasks"}
    menu_items[:] = [i for i in menu_items if i.name not in remove]


@hooks.register("register_admin_viewset")
def register_departure_viewset():
    from trips.models import DepartureViewSet

    return DepartureViewSet()