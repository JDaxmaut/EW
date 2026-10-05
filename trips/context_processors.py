from datetime import date

from django.conf import settings

from trips.requisites import bank_line, inn_line, parse_requisites, phone_href

MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

WEEKDAYS_SHORT = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def _plural(n, one, few, many):
    n = int(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return few
    return many


def date_ru(value):
    """12 июня 2026"""
    if not value:
        return ""
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def date_range_ru(start, end):
    """12–14 июня 2026 / 28 июня — 2 июля 2026"""
    if not start:
        return ""
    if not end or start == end:
        return date_ru(start)
    if start.year == end.year and start.month == end.month:
        return f"{start.day}–{end.day} {MONTHS[end.month - 1]} {end.year}"
    if start.year == end.year:
        return (
            f"{start.day} {MONTHS[start.month - 1]} — "
            f"{end.day} {MONTHS[end.month - 1]} {end.year}"
        )
    return f"{date_ru(start)} — {date_ru(end)}"


def price_ru(value):
    """1900 → «1 900»"""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value


def seats_phrase(n):
    return f"{n} {_plural(n, 'место', 'места', 'мест')}"


def static_version() -> str:
    """Время изменения site.js — чтобы браузер не держал старую копию."""
    from pathlib import Path

    try:
        path = Path(settings.BASE_DIR) / "static" / "js" / "site.js"
        return str(int(path.stat().st_mtime))
    except OSError:
        return "1"


def site_settings(request):
    from trips.models import (
        ContactPage,
        Departure,
        Destination,
        DestinationIndexPage,
        LegalPage,
    )

    today = date.today()

    legal_pages = list(
        LegalPage.objects.live().order_by("title")
    )
    legal_index = LegalPage.objects.filter(slug="legal").first()

    # Реквизиты и контакты — из раздела «РЕКВИЗИТЫ ТУРОПЕРАТОРА» оферты.
    offer = LegalPage.objects.filter(slug="offer").first()
    req = parse_requisites(offer.body) if offer else {}
    company_name = req.get("name") or getattr(settings, "COMPANY_NAME", "")
    company_inn = inn_line(req) or getattr(settings, "COMPANY_INN", "")
    bank_details = bank_line(req) or getattr(settings, "BANK_DETAILS", "")

    contact_page = ContactPage.objects.live().first()
    home = Destination.objects.live().order_by("title").first()

    telegram_url = getattr(settings, "TELEGRAM_URL", "")
    whatsapp_url = getattr(settings, "WHATSAPP_URL", "")
    max_url = getattr(settings, "MAX_URL", "")
    contact_href = contact_page.url if contact_page else "/contacts/"

    return {
        "YANDEX_METRIKA_ID": getattr(settings, "YANDEX_METRIKA_ID", ""),
        "TELEGRAM_URL": telegram_url,
        "WHATSAPP_URL": whatsapp_url,
        "MAX_URL": max_url,
        # Первый доступный мессенджер — для одиночных кнопок «Связаться».
        "MESSENGER_URL": telegram_url or whatsapp_url or max_url or contact_href,
        "CONTACT_HREF": contact_href,
        "SITE_NAME": getattr(settings, "SITE_NAME", ""),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", ""),
        "SITE_REGION": getattr(settings, "SITE_REGION", ""),
        "company_name": company_name,
        "company_inn": company_inn,
        "BANK_DETAILS": bank_details,
        "PHONE_HREF": phone_href(req) or getattr(settings, "PHONE_HREF", ""),
        "requisites": req,
        "legal_pages": legal_pages,
        "legal_index_url": legal_index.url if legal_index else "/legal/",
        "contact_page": contact_page,
        "footer_destinations": Destination.objects.live().order_by("title"),
        "nav_index": DestinationIndexPage.objects.live().first(),
        "nearest_departures": (
            Departure.objects.bookable()
            .select_related("destination")
            .order_by("start_date")[:6]
        ),
        "today": today,
        # Меняется при каждом правке site.js — браузер тянет свежую версию.
        "STATIC_VERSION": static_version(),
    }