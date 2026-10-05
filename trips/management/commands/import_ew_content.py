"""
Импорт контента из макета EWsite в CMS.

    python manage.py import_ew_content
    python manage.py import_ew_content --flush

Что переносит:
  1. **Направления** — из DIRECTIONS макета: название, тип, слоган, цена, дни,
     длительность, расстояние, особенности, описание, программа по часам,
     проживание, что входит/не входит, что взять, галерея, FAQ, метки.
  2. **Выезды** — из TRIPS: даты, цены, свободные места.
  3. **Юридические документы** — из LEGAL: заголовок, описание, дата и полный
     текст. Ровно пять документов, как в макете.
  4. **Главную** — тексты и блоки.
  5. **Контакты** — телефон, почта, адрес и мессенджеры из .env.

Данные читаются напрямую из build.py макета, поэтому ничего не теряется:
добавили в макет — повторили импорт.
"""

import datetime
import importlib.util
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from wagtail.models import Page

from trips.requisites import inn_line, parse_requisites
from trips.models import (
    AboutPage,
    ContactPage,
    Departure,
    Destination,
    DestinationIndexPage,
    HomePage,
    InfoPage,
    LegalPage,
)

EW = Path(r"C:\Users\dxmta\Desktop\EWsite")

KIND_BY_TYPE = {
    "micro": Destination.Kind.WILD_BEACH,
    "wild": Destination.Kind.WILD_BEACH,
    "beach": Destination.Kind.BEACH,
    "mountain": Destination.Kind.MOUNTAINS,
    "city": Destination.Kind.CITY,
}

KIND_LABEL = {
    "micro": "микропляж",
    "wild": "дикий пляж",
    "beach": "пляж",
    "mountain": "горы",
    "city": "город",
}

DURATION_LABEL = {
    "day": "один день",
    "night": "с ночёвкой",
    "2days": "два дня / одна ночь",
}

MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def load_ew():
    """Загружаем build.py как модуль, не выполняя main() — там есть guard."""
    spec = importlib.util.spec_from_file_location("ew_build", EW / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_date(value):
    """date/str('2026-10-09')/'14.06'/'5 июля' → date."""
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = str(value).strip().lower()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.?(\d{4})?$", text)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else timezone.now().year
        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None
    for index, name in enumerate(MONTHS, start=1):
        if name in text:
            m = re.match(r"^(\d{1,2})", text)
            if m:
                year = timezone.now().year
                try:
                    return timezone.datetime(year, index, int(m.group(1))).date()
                except ValueError:
                    return None
    return None


class Command(BaseCommand):
    help = "Переносит направления, выезды и документы из макета EWsite в CMS"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="перезаписать существующие")

    # ── служебное ──────────────────────────────────────────────
    def bullets(self, items):
        """Список строк → формат StreamField с одним ListBlock."""
        return [("items", [{"value": str(i)} for i in (items or [])])]

    def program_blocks(self, steps, day_imgs=None):
        from trips.blocks import DayBlock

        day_imgs = day_imgs or {}
        blocks = []
        for index, (time, title, text) in enumerate(steps or [], start=1):
            if time == "-":
                continue
            blocks.append((
                "day",
                {
                    "day_number": index,
                    "title": f"{time} — {title}" if time else title,
                    "text": f"<p>{text}</p>",
                    "image": self.ew_image(day_imgs[index]) if day_imgs.get(index) else None,
                },
            ))
        return blocks

    def pick_list(self, source, item):
        """Список может быть общим или лежать в dict по slug — берём и так, и так."""
        if isinstance(source, dict):
            return source.get(item["slug"]) or source.get("_all") or []
        return source or []

    def stay_blocks(self, items):
        """Проживание в макете — кортежи (название, тип, текст)."""
        blocks = []
        for entry in items or []:
            if isinstance(entry, (tuple, list)):
                name = entry[0] if len(entry) > 0 else ""
                kind = entry[1] if len(entry) > 1 else ""
                text = entry[2] if len(entry) > 2 else ""
            else:
                name = entry.get("name", "")
                kind = entry.get("kind", "")
                text = entry.get("text", "")
            blocks.append(("place", {"name": name, "kind": kind, "text": text}))
        return blocks

    def ew_image(self, key):
        """Картинка макета по ключу ('wall-waves') → объект Wagtail Images.

        Файл лежит в static/img/ew. Создаём один раз и переиспользуем:
        один и тот же кадр может стоять в галерее нескольких направлений.
        """
        from django.core.files import File
        from PIL import Image as PILImage
        from wagtail.images import get_image_model

        Image = get_image_model()
        title = f"EW — {key}"
        existing = Image.objects.filter(title=title).first()
        if existing:
            return existing

        path = Path(settings.BASE_DIR) / "static" / "img" / "ew" / f"{key}.webp"
        if not path.exists():
            return None
        with PILImage.open(path) as probe:
            width, height = probe.size
        with open(path, "rb") as fh:
            return Image.objects.create(
                title=title, file=File(fh, name=path.name), width=width, height=height
            )

    def gallery_blocks(self, keys):
        """Ключи картинок макета → блоки StreamField с изображениями."""
        blocks = []
        for key in keys or []:
            image = self.ew_image(key)
            if image:
                blocks.append(("image", image))
        return blocks

    # ── направления ────────────────────────────────────────────
    def handle(self, *args, **options):
        if not (EW / "build.py").exists():
            self.stderr.write(f"Не найден макет: {EW}")
            return

        ew = load_ew()
        index = DestinationIndexPage.objects.first()
        if index is None:
            self.stderr.write("Сначала выполните manage.py seed — нужен каталог направлений.")
            return

        if options["flush"]:
            Departure.objects.all().delete()
            Destination.objects.all().delete()
            self.stdout.write("· прежние направления удалены")

        count = 0
        for item in ew.DIRECTIONS:
            page = Destination.objects.filter(slug=item["slug"]).first()
            if page is None:
                page = Destination(slug=item["slug"], title=item["name"])

            page.title = item["name"]
            page.subtitle = item.get("tagline", "")
            page.kind = KIND_BY_TYPE.get(item.get("type"), Destination.Kind.BEACH)
            page.ew_type = item.get("type", "beach")
            page.ew_duration = item.get("duration", "day")
            page.ew_days = ", ".join(item.get("days") or [])
            page.distance_km = item.get("km") or None
            page.eyebrow = f"{SITE_REGION_SHORT} · {'выезды: ' + ', '.join(item.get('days', []))}"
            page.price_from = f"{item['price']:,}".replace(",", " ")
            page.duration = DURATION_LABEL.get(item.get("duration", "day"), "один день")
            page.distance = f"{item['km']} км" if item.get("km") else ""
            page.travel_time = ""
            page.parking = ""
            page.summary = (item.get("desc") or [""])[0]
            page.description = "".join(f"<p>{p}</p>" for p in item.get("desc") or [])
            page.search_description = (
                f"{item['name']} — {item.get('tagline','')}. "
                f"{page.distance}, поездка от {page.price_from} ₽."
            )

            page.highlights = self.bullets(item.get("highlights"))
            page.included = self.bullets(self.pick_list(ew.INCLUDED, item))
            page.excluded = self.bullets(self.pick_list(ew.EXCLUDED, item))
            page.packing = self.bullets(item.get("take"))
            page.programme = self.program_blocks(item.get("program"), item.get("day_imgs"))
            page.stay = self.stay_blocks(item.get("accommodation"))

            # Галерея направления: обложка + hero_extra + фото дней программы
            gallery_keys = [f"dest-{item['slug']}"]
            gallery_keys += list(item.get("hero_extra") or [])
            gallery_keys += list((item.get("day_imgs") or {}).values())
            seen = []
            for key in gallery_keys:
                if key not in seen:
                    seen.append(key)
            page.gallery = self.gallery_blocks(seen)
            page.gallery_hero = self.gallery_blocks(seen[:3])
            if item.get("faq"):
                page.faq = [
                    ("faq", {"question": q, "answer": a}) for q, a in item["faq"]
                ]

            if page.pk:
                page.save()
            else:
                index.add_child(instance=page)
            page.save_revision().publish()

            count += 1
            self.stdout.write(self.style.SUCCESS(f"+ направление «{item['name']}»"))

            self.import_trips(ew, page, item)

        self.import_legal(ew, count)
        self.import_home(ew)
        self.import_about(ew)
        self.import_contacts()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Импорт завершён."))

    # ── выезды ─────────────────────────────────────────────────
    def import_trips(self, ew, page, item):
        trips = [t for t in ew.TRIPS if t.get("dir") == item["slug"]]
        if not trips:
            return
        created = 0
        for trip in trips:
            start = parse_date(trip.get("date"))
            if start is None:
                self.stderr.write(
                    f"    ! не удалось разобрать дату выезда: {trip.get('date')!r}"
                )
                continue
            Departure.objects.update_or_create(
                destination=page,
                start_date=start,
                defaults={
                    "price": trip.get("price") or item["price"],
                    "seats_total": trip.get("total", 18),
                    "seats_left": trip.get("free", trip.get("total", 18)),
                    "meeting_point": "ТЦ «Галерея», парковка у центрального входа",
                    "status": Departure.Status.PLANNED,
                },
            )
            created += 1
        self.stdout.write(f"    · выездов в расписании: {created}")

    # ── документы ───────────────────────────────────────────────
    def import_legal(self, ew, offset):
        for doc in ew.LEGAL:
            page = LegalPage.objects.filter(slug=doc["slug"]).first()
            if page is None:
                page = LegalPage(slug=doc["slug"], title=doc["title"])
            page.title = doc["title"]
            page.intro = doc.get("short", "")
            page.updated = "октябрь 2026"
            page.body = doc.get("body", "")
            if page.pk:
                page.save()
            else:
                self.attach_legal(page)
            page.save_revision().publish()
            self.stdout.write(self.style.SUCCESS(f"+ документ «{doc['title'][:44]}»"))

    def attach_legal(self, page):
        """Документы — дети корня сайта, рядом с каталогом."""
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first()
        root = site.root_page if site else Page.objects.filter(depth=1).first()
        if page.is_descendant_of(root):
            page.move(root, "last-child")
        else:
            root.add_child(instance=page)

    # ── главная ────────────────────────────────────────────────
    def import_home(self, ew):
        page = HomePage.objects.first()
        if not page:
            return
        page.hero_eyebrow = f"{SITE_REGION_SHORT} · выезды каждые выходные"
        page.hero_title = "Нескучные выходные"
        page.hero_subtitle = (
            "Собираем группу и едем на море. Пляж, горы, микропляжи — на один день "
            "или с ночёвкой. Выходим в 6 утра, возвращаемся к девяти вечера."
        )
        page.hero_cta_text = "Смотреть направления"
        page.search_description = (
            "Поездки выходного дня на море по Краснодарскому краю: пляжи, горы, "
            "микропляжи. Небольшие группы, выезды каждую неделю."
        )
        page.save_revision().publish()
        self.stdout.write(self.style.SUCCESS("~ главная: тексты обновлены"))

    def import_about(self, ew):
        page = AboutPage.objects.first()
        if not page:
            return
        page.intro = (
            "Мы небольшая команда, которая каждую неделю собирает людей и увозит "
            "их на побережье."
        )
        page.body = (
            "<p>«Нескучные выходные» — это поездки выходного дня по Краснодарскому краю "
            "и короткие туры с ночёвкой. Мы не работаем с пляжами по всему миру: зато "
            "знаем каждое место, которое показываем.</p>"
            "<p>Формат простой: выезд в субботу утром, возвращение в тот же день вечером. "
            "Группа до 18 человек, автобус и сопровождающий. Если рядом живёте с детьми "
            "или без автомобиля — это ровно наш вариант.</p>"
        )
        offer = LegalPage.objects.filter(slug="offer").first()
        req = parse_requisites(offer.body) if offer else {}
        name = req.get("name") or COMPANY
        ids = inn_line(req) or INN
        page.details = (
            f"<p><strong>Реквизиты</strong><br>{name}<br>{ids}</p>"
            "<p>При отмене за 5 и более дней до выезда возвращаем всю сумму.</p>"
        )
        page.figures = [
            ("figure", {"value": "7 лет", "label": "возим людей по краю каждые выходные"}),
            ("figure", {"value": "1 240", "label": "гостей съездили с нами хотя бы раз"}),
            ("figure", {"value": "10", "label": "направлений в сезоне; из них 2 в подготовке"}),
            ("figure", {"value": "40 max", "label": "человек в группе — и то только на пляжных"}),
        ]
        page.save_revision().publish()
        self.stdout.write(self.style.SUCCESS("~ о нас: тексты обновлены"))

    def import_contacts(self):
        """Телефон, почта и адрес — из раздела «РЕКВИЗИТЫ ТУРОПЕРАТОРА» оферты.

        Мессенджеры в договоре не перечислены, поэтому берутся из .env.
        """
        page = ContactPage.objects.first()
        if not page:
            self.stdout.write("· страница контактов не найдена — пропускаю")
            return

        offer = LegalPage.objects.filter(slug="offer").first()
        req = parse_requisites(offer.body) if offer else {}
        if req:
            page.phone = req.get("phone", page.phone)
            page.email = req.get("email", page.email)
            page.address = req.get("address", page.address)
        else:
            page.phone = getattr(settings, "PHONE", page.phone)
            page.email = getattr(settings, "EMAIL", page.email)
            page.address = getattr(settings, "ADDRESS", page.address)
            self.stdout.write(self.style.WARNING(
                "· раздел «РЕКВИЗИТЫ ТУРОПЕРАТОРА» не найден — контакты из .env"
            ))

        page.telegram = getattr(settings, "TELEGRAM_URL", "")
        page.whatsapp = getattr(settings, "WHATSAPP_URL", "")
        page.max_link = getattr(settings, "MAX_URL", "")
        page.save_revision().publish()
        source = "из оферты" if req else "из .env"
        self.stdout.write(self.style.SUCCESS(f"~ контакты: обновлены {source}"))


SITE_REGION_SHORT = "Краснодарский край"
COMPANY = "ООО ТТЦ «Нескучные выходные»"
INN = "ИНН 2365039032 · ОГРН 1262300039231"