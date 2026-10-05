from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail import hooks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, TabbedInterface
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.blocks import CharBlock, ListBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page
from wagtail.search import index

from admin_ui.panels import DESTINATION_TABS, LEGAL_TABS

from . import blocks as tb

MONTHS_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


# ───────────────────────────── Выезд ─────────────────────────────

class DepartureQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(start_date__gte=date.today())

    def visible(self):
        return self.upcoming().exclude(status=Departure.Status.CANCELLED)

    def bookable(self):
        return self.visible().filter(status=Departure.Status.PLANNED, seats_left__gt=0)


class Departure(models.Model):
    """Один выезд на конкретную дату."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Планируется"
        SOLD_OUT = "sold_out", "Мест нет"
        CANCELLED = "cancelled", "Отменён"
        DONE = "done", "Прошёл"

    destination = ParentalKey(
        "Destination",
        on_delete=models.CASCADE,
        related_name="departures",
        verbose_name=_("Направление"),
    )
    start_date = models.DateField(
        _("Дата выезда"),
        help_text="День, когда группа собирается и выезжает.",
    )
    end_date = models.DateField(
        _("Дата возвращения"),
        null=True,
        blank=True,
        help_text="Для однодневных поездок можно оставить пустым.",
    )
    price = models.PositiveIntegerField(
        _("Цена за человека, ₽"),
        validators=[MinValueValidator(1)],
        help_text="Только число, без ₽. Например: 1900",
    )
    price_note = models.CharField(
        _("Пометка к цене"),
        max_length=80,
        blank=True,
        help_text="Например: «при бронировании за 3 дня −10%». Нет скидки — оставьте пустым.",
    )
    seats_total = models.PositiveSmallIntegerField(
        _("Всего мест"),
        default=40,
        validators=[MaxValueValidator(200)],
        help_text="Сколько человек помещается в автобус или группу.",
    )
    seats_left = models.PositiveSmallIntegerField(
        _("Свободно мест"),
        default=40,
        help_text="Сколько мест ещё можно продать.",
    )
    meeting_point = models.CharField(
        _("Где собираемся"),
        max_length=160,
        blank=True,
        help_text="Например: «ТЦ, парковка у фонтана, вход со стороны Movieplex».",
    )
    meeting_time = models.TimeField(
        _("Время сбора"),
        null=True,
        blank=True,
        help_text="Во сколько участники должны быть на месте.",
    )
    status = models.CharField(
        _("Состояние"),
        max_length=16,
        choices=Status.choices,
        default=Status.PLANNED,
        help_text=(
            "«Мест нет» — выезд виден в расписании с пометкой. "
            "«Отменён» — не показывается на сайте."
        ),
    )
    note = models.TextField(
        _("Комментарий для команды"),
        blank=True,
        help_text="Служебное поле. На сайте не выводится.",
    )

    objects = DepartureQuerySet.as_manager()

    class Meta:
        verbose_name = _("выезд")
        verbose_name_plural = _("выезды")
        ordering = ["start_date"]
        indexes = [models.Index(fields=["start_date", "status"])]

    def __str__(self):
        return f"{self.destination.title} — {self.start_date:%d.%m.%Y}"

    def clean(self):
        errors = {}
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "Дата возвращения не может быть раньше даты выезда."
        if self.seats_total is not None and self.seats_left is not None:
            if self.seats_left > self.seats_total:
                errors["seats_left"] = "Свободных мест не может быть больше, чем всего мест."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.status == Departure.Status.SOLD_OUT or self.seats_left == 0:
            if self.status != Departure.Status.CANCELLED:
                self.status = Departure.Status.SOLD_OUT
                self.seats_left = 0
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        return bool(self.start_date and self.start_date >= date.today())

    @property
    def is_bookable(self):
        return (
            self.is_upcoming
            and self.status == Departure.Status.PLANNED
            and self.seats_left > 0
        )

    @property
    def date_label(self):
        if not self.start_date:
            return "—"
        if not self.end_date or self.end_date == self.start_date:
            return f"{self.start_date.day} {MONTHS_GEN[self.start_date.month - 1]}"
        if self.start_date.month == self.end_date.month:
            return (
                f"{self.start_date.day}–{self.end_date.day} "
                f"{MONTHS_GEN[self.end_date.month - 1]}"
            )
        return (
            f"{self.start_date.day} {MONTHS_GEN[self.start_date.month - 1]} — "
            f"{self.end_date.day} {MONTHS_GEN[self.end_date.month - 1]}"
        )

    @property
    def weekday_label(self):
        return WEEKDAYS[self.start_date.weekday()] if self.start_date else ""

    @property
    def date_range_ru(self):
        if not self.start_date:
            return "Дата уточняется"
        if not self.end_date or self.end_date == self.start_date:
            return f"{self.date_label} ({self.weekday_label})"
        return (
            f"{self.date_label}: {self.start_date.day} "
            f"{MONTHS_GEN[self.start_date.month - 1]} — "
            f"{self.end_date.day} {MONTHS_GEN[self.end_date.month - 1]}"
        )


# ─────────────────────── Направление (страница) ───────────────────────

class DestinationTag(TaggedItemBase):
    content_object = ParentalKey(
        "Destination",
        related_name="tagged_items",
        on_delete=models.CASCADE,
        verbose_name=_("направление"),
    )

    class Meta:
        verbose_name = _("метка направления")
        verbose_name_plural = _("метки направлений")


class Destination(Page, ClusterableModel):
    class Kind(models.TextChoices):
        BEACH = "beach", "Пляж"
        WILD_BEACH = "wild_beach", "Дикий пляж"
        MOUNTAINS = "mountains", "Горы"
        CITY = "city", "Город"

    class Format(models.TextChoices):
        """Формат поездки — не то же самое, что тип места."""

        ONE_DAY = "one_day", "Однодневный"
        OVERNIGHT = "overnight", "С ночёвкой"
        EXCURSION = "excursion", "Экскурсия"

    ew_type = models.CharField(
        _("Тип по макету"),
        max_length=16,
        default="beach",
        help_text="Ключ фильтра каталога: micro, wild, beach, mountain, city.",
    )
    ew_duration = models.CharField(
        _("Длительность по макету"),
        max_length=16,
        default="day",
        help_text="day — один день, night — с ночёвкой.",
    )
    ew_days = models.CharField(
        _("Дни выездов"),
        max_length=40,
        blank=True,
        help_text="Через запятую, как в макете: «пт,сб,вс».",
    )
    distance_km = models.PositiveIntegerField(
        _("Расстояние, км"),
        null=True,
        blank=True,
        help_text="Числом — по нему работает фильтр «до 100 / 100–200 / дальше 200 км».",
    )

    subtitle = models.CharField(
        _("Подзаголовок"),
        max_length=160,
        blank=True,
        help_text="Короткая строка под названием. Например: «Дикий пляж в сосновом бору».",
    )
    kind = models.CharField(
        _("Тип"),
        max_length=16,
        choices=Kind.choices,
        default=Kind.BEACH,
        help_text="По типу фильтруется каталог. Он же подписывается плашкой на карточке.",
    )
    eyebrow = models.CharField(
        _("Надпись над заголовком"),
        max_length=80,
        blank=True,
        help_text="Например: «Анапа · 120 км от города». Можно оставить пустым.",
    )

    cover = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Обложка"),
        help_text="Главное фото направления. Без него карточка в каталоге будет пустой.",
    )
    price_from = models.CharField(
        _("Цена «от», ₽"),
        max_length=20,
        blank=True,
        help_text="Только число, можно с пробелом: 1 900. Без знака ₽.",
    )
    duration = models.CharField(
        _("Длительность"),
        max_length=60,
        default="1 день",
        help_text="Например: «1 день» или «2 дня / 1 ночь».",
    )
    format = models.CharField(
        _("Формат поездки"),
        max_length=16,
        choices=Format.choices,
        default=Format.ONE_DAY,
        help_text=(
            "Однодневный, с ночёвкой или экскурсия. От формата зависит заголовок "
            "программы на странице тура."
        ),
    )
    distance = models.CharField(
        _("Расстояние"),
        max_length=40,
        blank=True,
        help_text="Например: «120 км».",
    )
    travel_time = models.CharField(
        _("Время в пути"),
        max_length=40,
        blank=True,
        help_text="Например: «2,5 ч».",
    )
    parking = models.CharField(
        _("Парковка"),
        max_length=80,
        blank=True,
        help_text="Например: «платная, 300 ₽/день».",
    )

    summary = models.TextField(
        _("Коротко о направлении"),
        blank=True,
        help_text="Одно-два предложения: что это и зачем сюда ехать.",
    )
    description = RichTextField(
        _("Подробное описание"),
        blank=True,
        help_text="Развёрнутый текст: что там, чем отличается, что увидит человек.",
    )
    highlights = StreamField(
        *tb.bullet_stream(
            "Особенности",
            "4–7 коротких пунктов. Показываются списком с бирюзовыми точками.",
        ),
        blank=True,
    )
    included = StreamField(
        *tb.bullet_stream("Что входит", "Трансфер, гид, вода, страховка. По одному пункту."),
        blank=True,
    )
    excluded = StreamField(
        *tb.bullet_stream("Что не входит", "Обед, сувениры, личные расходы. По одному пункту."),
        blank=True,
    )
    faq = StreamField(
        *tb.qa_stream(
            "Частые вопросы",
            "3–4 вопроса, которые задают чаще всего. Отвечайте как в чате.",
        ),
        blank=True,
    )
    packing = StreamField(
        *tb.bullet_stream(
            "Что взять с собой",
            "6–10 пунктов: купальник, полотенце, деньги на парковку.",
        ),
        blank=True,
    )
    timeline = StreamField(
        [("step", tb.TimelineStepBlock())],
        blank=True,
        verbose_name=_("Линия времени"),
        help_text=(
            "Программа по часам: «6:00 — Сбор», «13:00 — Обед» и так далее. "
            "Порядок блоков и есть порядок шагов."
        ),
    )
    programme = StreamField(
        [("day", tb.DayBlock())],
        blank=True,
        verbose_name=_("Программа по дням"),
        help_text="Только для поездок с ночёвкой. Для однодневных не нужно.",
    )
    stay = StreamField(
        [("place", tb.StayBlock())],
        blank=True,
        verbose_name=_("Где остановиться"),
        help_text="Для поездок с ночёвкой: гостиница, апартаменты, коттедж.",
    )
    gallery_hero = StreamField(
        [("image", ImageChooserBlock(label="Фото"))],
        blank=True,
        verbose_name=_("Фото для первого экрана"),
        help_text="3–6 широких фотографий. Первая идёт на первый экран страницы.",
    )
    gallery = StreamField(
        [("image", ImageChooserBlock(label="Фото"))],
        blank=True,
        verbose_name=_("Галерея"),
        help_text="До 10 фотографий. Первые 4–5 соберут мозаику на странице.",
    )

    template = "pages/destination_page.html"

    departures = InlinePanel(
        "Departure",
        label=_("Выезды"),
        heading=_("Расписание выездов"),
    )

    tags = ClusterTaggableManager(
        through=DestinationTag, blank=True, verbose_name=_("Метки")
    )

    search_fields = Page.search_fields + [
        index.SearchField("subtitle"),
        index.SearchField("summary"),
        index.SearchField("distance"),
        index.SearchField("travel_time"),
    ]

    class Meta:
        verbose_name = _("направление")
        verbose_name_plural = _("направления")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["departures"] = self.departures.visible().order_by("start_date")
        context["bookable_departures"] = context["departures"].filter(
            status=Departure.Status.PLANNED, seats_left__gt=0
        )
        context["kind_labels"] = self.Kind.choices

        # Плоские списки для шаблонов: highlights, included, excluded, packing
        context["highlights"] = self.flat(self.highlights)
        context["included"] = self.flat(self.included)
        context["excluded"] = self.flat(self.excluded)
        context["packing"] = self.flat(self.packing)

        # Ближайшая дата — строкой, как в макете
        upcoming = context["departures"].first()
        context["next_date"] = upcoming.date_label if upcoming else ""
        context["hero_photos"] = [b.value for b in self.gallery_hero[:3]]
        context["wall_photos"] = [b.value for b in self.gallery[:4]]
        context["siblings"] = (
            Destination.objects.live()
            .exclude(pk=self.pk)
            .order_by("?")[:3]
        )
        return context

    # ── чек-лист готовности для админки ─────────────────────────
    CRITICAL_KEYS = {"cover", "price", "departures", "summary"}

    def completeness_items(self):
        departures = self.departures.upcoming()
        hero_count = len(self.gallery_hero)
        return [
            {"key": "title", "label": "Название направления",
             "done": bool(self.title), "anchor": "id_title"},
            {"key": "cover", "label": "Обложка — без неё карточка пустая",
             "done": bool(self.cover), "anchor": "id_cover"},
            {"key": "hero",
             "label": f"Фото для первого экрана: минимум 3, сейчас {hero_count}",
             "done": hero_count >= 3, "anchor": "id_gallery_hero"},
            {"key": "summary",
             "label": "Короткое описание: от 80 символов",
             "done": len((self.summary or "").strip()) >= 80, "anchor": "id_summary"},
            {"key": "price", "label": "Цена «от» и длительность",
             "done": bool(self.price_from and self.duration), "anchor": "id_price_from"},
            {"key": "departures", "label": "Хотя бы один выезд в расписании",
             "done": departures.exists(), "anchor": "id_departures"},
            {"key": "packing", "label": "Что взять с собой: минимум 3 пункта",
             "done": len(self.packing) >= 3, "anchor": "id_packing"},
            {"key": "seo", "label": "Заголовок для поиска",
             "done": bool(self.search_description), "anchor": "id_seo"},
        ]

    # ── списки для шаблонов ─────────────────────────────────
    @staticmethod
    def flat(stream):
        """StreamField с одним ListBlock → плоский список строк.

        В шаблоне {{ item }} должен печатать текст, а не словарь блока.
        """
        out = []
        for block in stream:
            value = getattr(block, "value", block)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                for entry in value:
                    if isinstance(entry, dict):
                        out.append(entry.get("value", ""))
                    else:
                        out.append(getattr(entry, "value", entry))
            else:
                out.append(value)
        return out

    @property
    def is_stub(self):
        """Заглушка: направление объявлено, но расписания ещё нет."""
        return not self.departures.upcoming().exists()

    @property
    def is_complete(self):
        return not self.is_stub

    @property
    def next_departure(self):
        return self.departures.upcoming().filter(
            status=Departure.Status.PLANNED, seats_left__gt=0
        ).first()

    @property
    def ew_days_list(self):
        return [d.strip() for d in self.ew_days.split(",") if d.strip()]

    @property
    def days_away(self):
        """Сколько дней до ближайшего выезда — для фильтра по дате."""
        dep = self.next_departure
        if not dep or not dep.start_date:
            return ""
        return (dep.start_date - date.today()).days

    @property
    def ew_distance_bucket(self):
        """near — до 100 км, mid — 100–200, far — дальше 200."""
        if not self.distance_km:
            return ""
        if self.distance_km <= 100:
            return "near"
        if self.distance_km <= 200:
            return "mid"
        return "far"

    @property
    def ew_type_label(self):
        return {
            "micro": "микропляж",
            "wild": "дикий пляж",
            "beach": "пляж",
            "mountain": "горы",
            "city": "город",
        }.get(self.ew_type, self.get_kind_display())

    @property
    def timeline_heading(self):
        """Заголовок программы — зависит от формата поездки."""
        return {
            self.Format.EXCURSION: ("Маршрут экскурсии", "по часам"),
            self.Format.OVERNIGHT: ("Программа поездки", "день за днём"),
        }.get(self.format, ("Программа дня", "по часам"))

    def completeness_percent(self):
        items = self.completeness_items()
        return round(sum(1 for i in items if i["done"]) / len(items) * 100)


class DestinationIndexPage(Page):
    """Каталог направлений."""

    intro = models.TextField(
        _("Вступление"),
        blank=True,
        help_text="Одно-два предложения под заголовком каталога.",
    )

    template = "pages/destination_index_page.html"

    subpage_types = {"Destination"}

    class Meta:
        verbose_name = _("каталог направлений")
        verbose_name_plural = _("каталоги направлений")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["destinations"] = Destination.objects.live().child_of(self).order_by("title")
        context["kinds"] = Destination.Kind.choices
        return context


# ───────────────────────────── Главная ─────────────────────────────

class HomePage(Page):
    hero_eyebrow = models.CharField(
        _("Надпись над заголовком"),
        max_length=80,
        default="Краснодарский край · выезды каждые выходные",
    )
    hero_title = models.CharField(
        _("Заголовок первого экрана"),
        max_length=80,
        default="Нескучные выходные",
    )
    hero_subtitle = models.TextField(
        _("Подзаголовок"),
        blank=True,
        help_text="Одно-два предложения: что это и ради чего.",
    )
    hero_cta_text = models.CharField(
        _("Текст главной кнопки"),
        max_length=40,
        default="Смотреть направления",
    )
    hero_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Большое фото первого экрана"),
        help_text="Широкое фото 2400×1400 или шире — левая часть коллажа.",
    )
    hero_images = StreamField(
        [("image", ImageChooserBlock(label="Фото"))],
        blank=True,
        verbose_name=_("Остальные фото коллажа"),
        help_text="2–3 фото для правой части первого экрана.",
    )

    template = "pages/home_page.html"

    body = StreamField(
        [
            ("nearest", tb.NearestDeparturesBlock()),
            ("manifest", tb.ManifestBlock()),
            ("grid", tb.DestinationGridBlock()),
            ("steps", tb.StepsBlock()),
            ("photos", tb.PhotoWallBlock()),
            ("features", tb.FeaturesBlock()),
            ("quote", tb.QuoteBlock()),
            ("faq", tb.FaqBlock()),
            ("cta", tb.CtaBlock()),
        ],
        blank=True,
        verbose_name=_("Блоки страницы"),
        help_text="Главная собирается из блоков. Их можно менять местами и удалять.",
    )

    class Meta:
        verbose_name = _("главная")
        verbose_name_plural = _("главные")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["nearest_departures"] = (
            Departure.objects.bookable()
            .select_related("destination")
            .order_by("start_date")[:8]
        )
        context["featured_destinations"] = Destination.objects.live().order_by("title")[:6]
        return context


# ───────────────────────────── Страницы ─────────────────────────────

class AboutPage(Page):
    template = "pages/about_page.html"

    intro = models.TextField(_("Вступление"), blank=True)
    body = RichTextField(_("О клубе"), blank=True)
    figures = StreamField(
        [("figure", tb.FigureBlock())],
        blank=True,
        verbose_name=_("Цифры"),
        help_text="Например: 6 лет возим, 1200 довольных клиентов, 40+ выездов за сезон.",
    )
    gallery = StreamField(
        [("image", ImageChooserBlock(label="Фото"))],
        blank=True,
        verbose_name=_("Фотографии"),
        help_text="Команда, автобусы, наши выезды.",
    )
    details = RichTextField(
        _("Реквизиты и подробности"),
        blank=True,
        help_text="ИНН, ОГРН, банковские реквизиты, режим работы.",
    )

    class Meta:
        verbose_name = _("о клубе")
        verbose_name_plural = _("о клубе")


class ContactPage(Page):
    template = "pages/contact_page.html"

    body = RichTextField(_("Текст перед формой"), blank=True)
    telegram = models.CharField(_("Telegram"), max_length=120, blank=True)
    whatsapp = models.CharField(_("WhatsApp"), max_length=120, blank=True)
    max_link = models.CharField(_("MAX"), max_length=200, blank=True)
    phone = models.CharField(_("Телефон"), max_length=60, blank=True)
    email = models.CharField(_("Почта"), max_length=120, blank=True)
    address = models.CharField(_("Город отправления"), max_length=120, blank=True)
    work_hours = models.CharField(
        _("Режим работы"),
        max_length=120,
        blank=True,
        help_text="Например: «ежедневно с 9:00 до 21:00».",
    )

    class Meta:
        verbose_name = _("контакты")
        verbose_name_plural = _("контакты")


class InfoPage(Page):
    template = "pages/info_page.html"
    """Как добраться: точки сбора, маршруты, что учесть."""

    body = RichTextField(_("Текст"), blank=True)
    meeting_points = StreamField(
        [("point", tb.MeetingPointBlock())],
        blank=True,
        verbose_name=_("Точки сбора"),
        help_text="Где и во сколько собираемся.",
    )
    notes = StreamField(
        [("note", tb.InfoNoteBlock())],
        blank=True,
        verbose_name=_("Что учесть"),
        help_text="Парковка, раздевалки, душ, питание, Wi-Fi.",
    )

    class Meta:
        verbose_name = _("как добраться")
        verbose_name_plural = _("как добраться")


class LegalPage(Page):
    template = "pages/legal_page.html"

    intro = models.TextField(_("Описание"), blank=True,
                            help_text="Одна строка для списка документов.")
    updated = models.CharField(_("Дата редакции"), max_length=60, default="октябрь 2026",
                               help_text="Например: «октябрь 2026». Показывается в списке и на странице.")
    body = RichTextField(_("Текст документа"), blank=True)

    class Meta:
        verbose_name = _("юридический документ")
        verbose_name_plural = _("юридические документы")


class ContactSubmission(models.Model):
    name = models.CharField(_("Имя"), max_length=120)
    phone = models.CharField(_("Телефон"), max_length=60, blank=True)
    email = models.EmailField(_("Почта"), blank=True)
    destination = models.CharField(
        _("Направление"),
        max_length=160,
        blank=True,
        help_text="Какое направление выбрал человек в форме.",
    )
    departure_date = models.CharField(
        _("Дата выезда"),
        max_length=60,
        blank=True,
        help_text="Какую дату выбрал человек в форме.",
    )
    message = models.TextField(_("Комментарий"), blank=True)
    created_at = models.DateTimeField(_("Получена"), auto_now_add=True)
    handled = models.BooleanField(_("Обработана"), default=False)

    class Meta:
        verbose_name = _("заявка")
        verbose_name_plural = _("заявки")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.created_at:%d.%m.%Y %H:%M}"


# ──────────────────── Админка выездов (список) ────────────────────

class DepartureViewSet(ModelViewSet):
    model = Departure
    icon = "date"
    menu_label = _("Выезды")
    menu_name = "trips_departures"
    add_to_admin_menu = False
    list_display = ["destination", "start_date", "price", "seats_left", "status"]
    list_filter = ["status", "destination__kind"]
    search_fields = ["destination__title", "meeting_point", "note"]
    ordering = ["start_date"]
    panels = [
        FieldPanel("destination"),
        MultiFieldPanel(
            [FieldPanel("start_date"), FieldPanel("end_date")],
            heading=_("Даты"),
        ),
        MultiFieldPanel(
            [FieldPanel("price"), FieldPanel("price_note")],
            heading=_("Цена"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("seats_total"),
                FieldPanel("seats_left"),
                FieldPanel("status"),
            ],
            heading=_("Места"),
        ),
        MultiFieldPanel(
            [FieldPanel("meeting_point"), FieldPanel("meeting_time")],
            heading=_("Сбор"),
        ),
        FieldPanel("note"),
    ]


# ───────────────────── Запрет преждевременной публикации ─────────────────────

@hooks.register("before_publish_page")
def block_incomplete_destination(page, request, *args, **kwargs):
    if not isinstance(page, Destination):
        return
    missing = [
        item["label"]
        for item in page.completeness_items()
        if not item["done"] and item["key"] in Destination.CRITICAL_KEYS
    ]
    if missing:
        raise ValueError("Нельзя опубликовать — не заполнено: " + ", ".join(missing) + ".")


# ───────────────────────────── Панели страниц ─────────────────────────────
# Вкладки с русскими подсказками живут в admin_ui/panels.py.
Destination.edit_handler = TabbedInterface(DESTINATION_TABS)
LegalPage.edit_handler = TabbedInterface(LEGAL_TABS)


HomePage.content_panels = [
    MultiFieldPanel(
        [
            FieldPanel("hero_eyebrow"),
            FieldPanel("hero_title"),
            FieldPanel("hero_subtitle"),
            FieldPanel("hero_cta_text"),
            FieldPanel("hero_image"),
            FieldPanel("hero_images"),
        ],
        heading=_("Первый экран"),
    ),
    FieldPanel("body"),
]

DestinationIndexPage.content_panels = [FieldPanel("intro")]

AboutPage.content_panels = [
    FieldPanel("intro"),
    FieldPanel("body"),
    FieldPanel("figures"),
    FieldPanel("gallery"),
    FieldPanel("details"),
]

ContactPage.content_panels = [
    FieldPanel("body"),
    MultiFieldPanel(
        [
            FieldPanel("telegram"),
            FieldPanel("whatsapp"),
            FieldPanel("max_link"),
        ],
        heading=_("Мессенджеры"),
    ),
    MultiFieldPanel(
        [
            FieldPanel("phone"),
            FieldPanel("email"),
            FieldPanel("address"),
            FieldPanel("work_hours"),
        ],
        heading=_("Контакты"),
    ),
]

InfoPage.content_panels = [
    FieldPanel("body"),
    FieldPanel("meeting_points"),
    FieldPanel("notes"),
]

ContactSubmission.panels = [
    FieldPanel("name"),
    FieldPanel("phone"),
    FieldPanel("email"),
    FieldPanel("destination"),
    FieldPanel("departure_date"),
    FieldPanel("message"),
    FieldPanel("handled"),
]
