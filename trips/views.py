from datetime import date

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .models import (
    ContactPage,
    ContactSubmission,
    Departure,
    Destination,
    HomePage,
)


def search(request):
    query = request.GET.get("q", "").strip()
    results = Destination.objects.none()
    if len(query) >= 2:
        results = (
            Destination.objects.live()
            .filter(
                Q(title__icontains=query)
                | Q(subtitle__icontains=query)
                | Q(summary__icontains=query)
                | Q(distance__icontains=query)
                | Q(tags__name__icontains=query)
            )
            .distinct()
            .order_by("title")
        )
    return render(
        request,
        "search.html",
        {
            "q": query,
            "results": results,
            "page": HomePage.objects.live().first(),  # базовый шаблон ждёт page
        },
    )


MONTH_LABELS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def schedule_view(request):
    """Живое расписание выездов — отдельная страница, сгруппированная по месяцам."""
    departures = (
        Departure.objects.upcoming()
        .exclude(status=Departure.Status.CANCELLED)
        .select_related("destination")
        .order_by("start_date")
    )

    months = []
    for dep in departures:
        key = (dep.start_date.year, dep.start_date.month)
        if key not in [m["key"] for m in months]:
            months.append(
                {
                    "key": key,
                    "label": f"{MONTH_LABELS[dep.start_date.month - 1]} {dep.start_date.year}",
                    "items": [],
                }
            )
        months[-1]["items"].append(dep)

    return render(
        request,
        "schedule.html",
        {
            "page": HomePage.objects.live().first(),
            "months": months,
            "departures": departures,
        },
    )


def legal_index_view(request):
    """Список всех юридических документов сайта."""
    from .models import LegalPage

    legal_pages = (
        LegalPage.objects.live().select_related("owner").order_by("title")
    )
    return render(
        request,
        "pages/legal_index_page.html",
        {
            "page": HomePage.objects.live().first(),
            "legal_pages": legal_pages,
        },
    )


def cookie_accept(request):
    """Принимает cookie и возвращает пользователя на ту же страницу.

    Согласие хранится в cookie, а не в localStorage: часть браузеров
    блокирует локальное хранилище, и баннер тогда появлялся на каждой странице.
    Работает даже с отключённым JavaScript.
    """
    target = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        target = "/"

    response = HttpResponseRedirect(target)
    response.set_cookie(
        "nw_cookie",
        "1",
        max_age=365 * 24 * 60 * 60,
        samesite="Lax",
        secure=request.is_secure(),
    )
    return response


def robots_txt(request):
    base = settings.WAGTAILADMIN_BASE_URL.rstrip("/")
    body = f"""User-agent: *
Disallow: /cms/
Disallow: /django-admin/
Disallow: /search/
Allow: /

Sitemap: {base}/sitemap.xml
"""
    return HttpResponse(body, content_type="text/plain")


@require_POST
def contact_submit(request):
    """Приём заявки с сайта. Работает и через AJAX, и обычной отправкой формы."""
    form = ContactForm(request.POST)

    if form.is_valid():
        # Не даём одному человеку создать сотню заявок подряд
        recent = ContactSubmission.objects.filter(
            phone=form.cleaned_data.get("phone") or ""
        ).count()
        if recent > 5:
            pass  # не блокируем, но и не падаем
        submission = form.save()
        payload = {
            "ok": True,
            "id": submission.pk,
            "message": "Заявка отправлена. Мы напишем вам в ближайшее время.",
        }
    else:
        payload = {
            "ok": False,
            "errors": {
                field: error[0] for field, errors in form.errors.items() for error in [errors]
            },
        }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(payload, status=200 if payload["ok"] else 400)

    contact_url = ContactPage.objects.live().first()
    return render(
        request,
        "pages/contact_page.html",
        {
            "page": contact_url,
            "sent": payload["ok"],
            "form": form,
            "errors": None if payload["ok"] else payload["errors"],
        },
    )