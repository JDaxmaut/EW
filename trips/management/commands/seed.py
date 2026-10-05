"""
Наполнение сайта: служебные страницы, 8 направлений и расписание выездов.

    python manage.py seed
    python manage.py seed --flush

Фотографии берутся из media/stock/<slug>-*.jpg, если они есть (их загружает
команда fetch_stock_photos). Если нет — подставляются бирюзовые плейсхолдеры
из media/placeholders, чтобы сайт не выглядел сломанным.
"""

from datetime import date, datetime, time, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image as PILImage
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from trips import blocks as tb
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

# ── Справочник направлений ──────────────────────────────────────
# Подписи и цены взяты из SITE_PROMPT.md §5 — чтобы тексты на сайте
# были осмысленными, а не «Lorem ipsum».

DESTINATIONS = [
    {
        "title": "Ханская",
        "slug": "hanskaya",
        "subtitle": "Дикий песок между скалами",
        "kind": Destination.Kind.WILD_BEACH,
        "eyebrow": "Анапа · 120 км",
        "price_from": "1 900",
        "duration": "1 день",
        "distance": "120 км",
        "travel_time": "2,5 ч",
        "parking": "бесплатно",
        "summary": (
            "Пляж, о котором почти никто не знает: мелкий золотистый песок между "
            "выступами известняка. Идём пешком от парковки минут двадцать, и вокруг "
            "почти никого. Ждём только до середины дня, когда солнце уходит."
        ),
        "description": (
            "<p>Ханская — это не про «курорт», а про пустое побережье и "
            "рисунок скал, который меняется вместе с уровнем воды. Мы приезжаем "
            "ранним утром, пока пляж ещё пустой, и уходим до обеда.</p>"
            "<p>Внизу — вода настолько прозрачная, что видно дно в двадцати "
            "метрах от берега. Для купания удобно ближе к скалам: там мельче "
            "и спокойнее, чем на открытом участке.</p>"
        ),
        "highlights": [
            "Дикий песок и скалы вместо построек",
            "Вода прозрачная до дна",
            "Небольшая группа — до 20 человек",
            "Ранний выезд, уезжаем до обеда",
        ],
        "included": ["Автобус туда и обратно", "Гид на весь день", "Питьевая вода", "Страховка"],
        "excluded": ["Обед и питание", "Полотенца и зонты", "Платный пляж, если он есть"],
        "packing": [
            "Купальник и полотенце",
            "Солнцезащитный крем",
            "Головной убор и солнцезащитные очки",
            "Резиновые тапочки для камней",
            "Свободная одежда для детей",
            "Наличные на парковку и воду",
        ],
    },
    {
        "title": "Дондуковская",
        "slug": "dondukovskaya",
        "subtitle": "Сосновый бор и пустое побережье",
        "kind": Destination.Kind.WILD_BEACH,
        "eyebrow": "Анапа · 135 км",
        "price_from": "1 700",
        "duration": "1 день",
        "distance": "135 км",
        "travel_time": "2,5 ч",
        "parking": "бесплатно, вдоль дороги",
        "summary": (
            "Дикий пляж за сосновым бором: дюны, сосны и пустое побережье, "
            "которое в выходные остаётся почти безлюдным. Самый спокойный вариант "
            "для тех, кто устал от организованных туров."
        ),
        "description": (
            "<p>Дондуковская — это дюны и сосновый бор прямо у воды. Купаться "
            "удобно в любом месте: берег ровный и пологий, поэтому вход в море "
            "безопален даже с детьми.</p>"
            "<p>На берегу нет кафе и душа, поэтому мы возим воду и перекус "
            "с собой. Зато вечером можно остаться у костра, если останется время "
            "и дождя не будет.</p>"
        ),
        "highlights": [
            "Пустое побережье без толпы",
            "Сосновый бор до самой кромки воды",
            "Пологий безопасный вход в море",
            "Подходит с детьми",
        ],
        "included": ["Автобус туда и обратно", "Гид на весь день", "Вода и перекус", "Страховка"],
        "excluded": ["Обед", "Аренда пляжных принадлежностей"],
        "packing": [
            "Купальник и полотенце",
            "Полотенце на песок",
            "Кепка от солнца",
            "Детский надувной круг",
            "Свободная одежда для детей",
            "Мусорный пакет",
        ],
    },
    {
        "title": "Гиагинская",
        "slug": "giaginskaya",
        "subtitle": "Широкий мелководный пляж",
        "kind": Destination.Kind.BEACH,
        "eyebrow": "Геленджикский район · 170 км",
        "price_from": "1 900",
        "duration": "1 день",
        "distance": "170 км",
        "travel_time": "3 ч",
        "parking": "платная, 200 ₽/день",
        "summary": (
            "Классический широкий пляж с мелкой пологой полосой: в море можно "
            "зайти на десятки метров и не бояться глубины. Самый спокойный выбор "
            "для первого знакомства с побережьем."
        ),
        "description": (
            "<p>Гиагинская — простой и понятный пляж: песок, пологий вход, "
            "несколько кафе и раздевалка. Именно сюда мы возим тех, кто едет "
            "впервые и боится «дорогого» формата.</p>"
            "<p>Пляж протяжённый, поэтому даже в разгар сезона легко найти "
            "место в стороне от центрального участка.</p>"
        ),
        "highlights": [
            "Мелководная безопасная полоса",
            "Инфраструктура: кафе, раздевалки, душ",
            "Подходит семьям с маленькими детьми",
            "Широкий пляж — легко найти свободное место",
        ],
        "included": ["Автобус туда и обратно", "Сопровождающий", "Страховка"],
        "excluded": ["Еда и напитки", "Платная парковка", "Шезлонги и зонты"],
        "packing": [
            "Купальник, полотенце",
            "Резиновые тапочки",
            "Панамная шляпа",
            "Деньги на парковку",
            "Легкий перекус и вода",
        ],
    },
    {
        "title": "Лабинск",
        "slug": "labinsk",
        "subtitle": "Набережная, кофе и самый короткий выезд",
        "kind": Destination.Kind.CITY,
        "eyebrow": "Кубань · 100 км",
        "price_from": "1 400",
        "duration": "1 день",
        "distance": "100 км",
        "travel_time": "2 ч",
        "parking": "бесплатно в центре",
        "summary": (
            "Городская набережная вместо пляжа: зелёная зона вдоль реки, "
            "прогулки, кофе и спокойный день без «клепалок». Самый короткий "
            "и самый лёгкий выезд."
        ),
        "description": (
            "<p>Этот выезд для тех, кому нужен день без пляжного полотенца. "
            "Набережная ухоженная, с тенями, лавочками и видом на воду — можно "
            "просто идти вдоль реки и останавливаться где нравится.</p>"
            "<p>В программе: прогулка по набережной, свободное время и обратная "
            "дорога к вечеру. Получается отличная поездка с родителями или "
            "коллегами.</p>"
        ),
        "highlights": [
            "Самая короткая дорога — всего два часа",
            "Ухоженная набережная с тенями",
            "Много кафе по маршруту",
            "Подходит без купальника",
        ],
        "included": ["Автобус туда и обратно", "Сопровождающий", "Страховка"],
        "excluded": ["Обед в кафе", "Сувениры"],
        "packing": ["Удобная обувь", "Солнцезащитные очки", "Небольшая сумка"],
    },
    {
        "title": "Майкоп",
        "slug": "maykop",
        "subtitle": "Плато, смотровые и воздух вместо пляжа",
        "kind": Destination.Kind.MOUNTAINS,
        "eyebrow": "Адыгея · 150 км",
        "price_from": "2 300",
        "duration": "1 день",
        "distance": "150 км",
        "travel_time": "3 ч",
        "parking": "бесплатно на площадках",
        "summary": (
            "Горы вместо моря: плато с видом на долину, сосновый воздух и "
            "несколько смотровых без серпантина и толп. Температура на десять "
            "градусов ниже, чем на побережье."
        ),
        "description": (
            "<p>Майкопский район — это не море, но самая прохладная и насыщенная "
            "прогулка в нашей подборке. Подъём несложный, дорога асфальтированная.</p>"
            "<p>На маршруте: смотровые площадки, сосновые аллеи, вторая половина "
            "дня — свободное время или пеший выход к обзорной точке по желанию.</p>"
        ),
        "highlights": [
            "Прохладно даже в жару",
            "Смотровые площадки без толп",
            "Сосновые леса и чистый воздух",
            "Небольшая группа и лёгкий выезд",
        ],
        "included": ["Автобус туда и обратно", "Гид-пешеход", "Вода и перекус", "Страховка"],
        "excluded": ["Обед", "Входные платежи на плато", "Метеоступки"],
        "packing": [
            "Удобная обувь для ходьбы",
            "Лёгкая куртка — на высоте прохладно",
            "Питьевая вода 1,5 литра",
            "Головной убор",
            "Крем от солнца",
        ],
    },
    {
        "title": "Белореченск",
        "slug": "belorechensk",
        "subtitle": "Ущелье, пещеры и зелень в часе от города",
        "kind": Destination.Kind.MOUNTAINS,
        "eyebrow": "Апшеронск · 110 км",
        "price_from": "2 100",
        "duration": "1 день",
        "distance": "110 км",
        "travel_time": "2,5 ч",
        "parking": "бесплатно",
        "summary": (
            "Горный空气 вместо пляжного часа: зелёное ущелье, пещеры и прохладная "
            "тень, до которой от города меньше двух часов на машине. Хороший "
            "вариант на случай, когда море не в планах."
        ),
        "description": (
            "<p>Это направление выбирают в жару: в ущелье на десять-двенадцать "
            "градусов прохладнее, чем на берегу, и нет толп.</p>"
            "<p>Маршрут без сложных переходов: поездка на канатке или пешком "
            "по размеченной тропе, осмотр грота, свободное время и обратный выезд.</p>"
        ),
        "highlights": [
            "Прохладно в самые жаркие дни",
            "Пещеры и ущелье",
            "Дорога короче, чем в горы на севере",
            "Можно без купальника",
        ],
        "included": ["Автобус туда и обратно", "Гид", "Вода и перекус", "Страховка"],
        "excluded": ["Обед", "Входные билеты в пещеры"],
        "packing": [
            "Удобная обувь с нескользящей подошвой",
            "Куртка от дождя",
            "Вода и лёгкий перекус",
            "Репеллент",
        ],
    },
    {
        "title": "Курганинск",
        "slug": "kurgansk",
        "subtitle": "Тихое побережье без толпы",
        "kind": Destination.Kind.BEACH,
        "eyebrow": "Азовское побережье · 160 км",
        "price_from": "1 600",
        "duration": "1 день",
        "distance": "160 км",
        "travel_time": "2,5 ч",
        "parking": "бесплатно",
        "summary": (
            "Мелкий тёплый пляж на Азовском побережье: вода прогревается быстрее, "
            "чем на Чёрном море, и людей заметно меньше. Короткий выезд для тех, "
            "кто хочет просто искупаться без программы."
        ),
        "description": (
            "<p>Курганинск — это про тишину и тёплую воду. Пляж песчано-ракушечный, "
            "мелкий, безопасный, с пологим входом.</p>"
            "<p>Инфраструктуры почти нет, поэтому выезд подходит тем, кто привык "
            "обходиться минимальным набором вещей и привезти всё с собой.</p>"
        ),
        "highlights": [
            "Тёплое мелководное море",
            "Мало людей",
            "Песчано-ракушечный берег",
            "Недорогой короткий выезд",
        ],
        "included": ["Автобус туда и обратно", "Сопровождающий", "Страховка"],
        "excluded": ["Обед", "Инфраструктура пляжа"],
        "packing": [
            "Купальник, полотенце",
            "Тапочки",
            "Кепка",
            "Свободная одежда для детей",
            "Вода и перекус",
        ],
    },
    {
        "title": "Краснодар",
        "slug": "krasnodar",
        "subtitle": "Городская набережная и вечерние прогулки",
        "kind": Destination.Kind.CITY,
        "eyebrow": "День в городе · 15 км",
        "price_from": "1 200",
        "duration": "1 день",
        "distance": "15 км",
        "travel_time": "40 мин",
        "parking": "платный в центре",
        "summary": (
            "Короткая поездка без переездов: набережная Кубани, городские парки, "
            "кофе и прогулка. Подходит, когда хочется сменить обстановку, не "
            "тратя целый день на дорогу."
        ),
        "description": (
            "<p>Краснодар — это вариант «просто вырваться из дома». Собираемся "
            "утром, гуляем по набережной и паркам, возвращаемся к вечеру.</p>"
            "<p>Формат подходит и тем, кто ещё не готов к морю, и тем, кому "
            "просто нужен день без работы.</p>"
        ),
        "highlights": [
            "Сорок минут в пути",
            "Набережная и парки",
            "Без пляжного инвентаря",
            "Можно с детьми любого возраста",
        ],
        "included": ["Трансфер", "Сопровождающий", "Страховка"],
        "excluded": ["Обед", "Билеты в музеи и кино"],
        "packing": ["Удобная обувь", "Вода", "Солнцезащитный крем"],
    },
]

# Служебные страницы
ABOUT_FIGURES = [
    ("6 лет", "возим каждую неделю"),
    ("1200+", "довольных участников"),
    ("40+", "выездов за сезон"),
    ("20", "человек в группе максимум"),
]


class Command(BaseCommand):
    help = "Создаёт страницы сайта, 8 направлений и расписание выездов"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true", help="удалить созданные ранее направления"
        )

    # ── утилиты ────────────────────────────────────────────────
    def image_model(self):
        return get_image_model()

    def find_photo(self, slug: str, kind: str = "card"):
        """Сток-фото, если есть, иначе плейсхолдер нужной пропорции."""
        root = Path(settings.MEDIA_ROOT)
        patterns = {
            "card": [f"stock/{slug}-card.*", f"stock/{slug}*.jpg", f"stock/{slug}*.jpeg",
                     f"stock/{slug}*.webp"],
            "hero": [f"stock/{slug}-hero.*", f"stock/{slug}*.jpg", f"stock/{slug}*.webp"],
            "square": [f"stock/{slug}-square.*", f"stock/{slug}*.jpg", f"stock/{slug}*.webp"],
        }
        for pattern in patterns.get(kind, patterns["card"]):
            for path in sorted(root.glob(pattern)):
                if path.is_file():
                    return path
        return None

    def placeholder(self, name: str):
        return Path(settings.MEDIA_ROOT) / "placeholders" / name

    def get_or_create_image(self, path: Path, title: str):
        if not path or not path.exists():
            return None
        Image = self.image_model()
        existing = Image.objects.filter(title=title).first()
        if existing:
            return existing
        with PILImage.open(path) as probe:
            width, height = probe.size
        with open(path, "rb") as fh:
            return Image.objects.create(
                title=title,
                file=File(fh, name=path.name),
                width=width,
                height=height,
            )

    def stock_pool(self, limit: int = 6):
        """Пул реальных фотографий из media/stock — по одной с каждого слота.

        Нужен для первого экрана: одно фото нельзя показывать трижды,
        а подбирать три разных «красивых» файла вручную долго.
        """
        root = Path(settings.MEDIA_ROOT) / "stock"
        if not root.exists():
            return []
        pool = []
        for pattern in ("*-hero.webp", "*-card.webp", "*-square.webp"):
            for path in sorted(root.glob(pattern)):
                if path not in pool:
                    pool.append(path)
        return pool[:limit]

    def make_image(self, slug: str, title: str, kind: str, fallback_placeholder: str):
        photo = self.find_photo(slug, kind)
        if photo:
            return self.get_or_create_image(photo, title)
        return self.get_or_create_image(self.placeholder(fallback_placeholder), title)

    # ── страницы ───────────────────────────────────────────────
    def handle(self, *args, **options):
        root = Page.objects.filter(depth=1).first()
        if not root:
            self.stderr.write("Нет корневой страницы. Сначала инициализируйте Wagtail.")
            return

        if options["flush"]:
            Destination.objects.all().delete()
            self.stdout.write("Направления удалены")

        # Главная становится корнем сайта: остальные страницы живут её детьми,
        # иначе Wagtail не сможет замаршрутизировать их адреса.
        home = self.ensure_home(root, force=options["flush"])
        index = self.ensure_index(home)
        self.ensure_about(home)
        self.ensure_contact(home)
        self.ensure_info(home)
        self.ensure_legal(home)
        self.ensure_groups()

        created = self.ensure_destinations(index)
        departures = self.ensure_departures(created)

        # Wagtail ищет сайт по hostname — ставим localhost, чтобы работало
        # и на 127.0.0.1, и на localhost при локальной разработке.
        site = Site.objects.filter(is_default_site=True).first()
        if site:
            site.port = 8000
            site.site_name = "Нескучные выходные"
            site.hostname = "localhost"
            site.root_page = home
            site.save()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Готово."))
        self.stdout.write(f"  Направлений: {len(created)}")
        self.stdout.write(f"  Выездов: {departures}")
        self.stdout.write("  Админка: /cms/ — войдите через createsuperuser")

    def ensure_index(self, home) -> DestinationIndexPage:
        index = DestinationIndexPage.objects.first()
        if not index:
            index = DestinationIndexPage(
                title="Направления",
                slug="catalog",
                intro="Восемь проверенных направлений: дикие пляжи, горы и города. "
                      "Выбирайте, куда поехать на этих выходных.",
                search_description="Поездки выходного дня по Краснодарскому краю: "
                                   "пляжи, горы, микропляжи. Бали не нужен.",
            )
            home.add_child(instance=index)
            index.save_revision().publish()
            self.stdout.write("+ каталог направлений")
        return index

    def ensure_home(self, root, force: bool = False) -> HomePage:
        home = HomePage.objects.first()
        if home and not force:
            return home

        # Три разных кадра из пула: повторять одно фото в коллаже нельзя
        pool = self.stock_pool(6)
        used = set()
        hero = hero_2 = hero_3 = None
        for index, (title, slot, fallback) in enumerate([
            ("Первый экран", "hero", "placeholder-hero-wide-2400x1400.webp"),
            ("Коллаж 2", "card", "placeholder-hero-2-800x600.webp"),
            ("Коллаж 3", "square", "placeholder-hero-3-800x1000.webp"),
        ]):
            source = next((p for p in pool if p not in used), None)
            if source:
                used.add(source)
            image = self.get_or_create_image(source, title) if source else None
            if image is None:
                image = self.make_image("home", title, slot, fallback)
            if index == 0:
                hero = image
            elif index == 1:
                hero_2 = image
            else:
                hero_3 = image

        if home:
            # Пересобираем первый экран на уже существующей странице:
            # удалять HomePage нельзя — это корень сайта, уйдёт всё дерево.
            home.hero_eyebrow = "Краснодарский край · выезды каждые выходные"
            home.hero_cta_text = "Смотреть направления"
            home.hero_title = "Нескучные выходные"
            home.hero_subtitle = (
                "Собираем группу и едем на море. Пляж, горы, микропляжи — "
                "на один день или с ночёвкой. Выходим в 6 утра, "
                "возвращаемся к девяти вечера."
            )
            home.hero_image = hero
            home.search_description = (
                "Поездки выходного дня на море по Краснодарскому краю. "
                "Небольшие группы, дикие пляжи, горы. Выезды каждую неделю."
            )

        home = home or HomePage(
            title="Нескучные выходные",
            slug="main",
            hero_eyebrow="Краснодарский край · выезды каждые выходные",
            hero_title="Нескучные выходные",
            hero_subtitle="Собираем группу и едем на море. Пляж, горы, микропляжи — "
                          "на один день или с ночёвкой. Выходим в 6 утра, "
                          "возвращаемся к девяти вечера.",
            hero_cta_text="Смотреть направления",
            hero_image=hero,
            search_description="Поездки выходного дня на море по Краснодарскому краю. "
                               "Небольшие группы, дикие пляжи, горы. Выезды каждую неделю.",
        )

        if hero_2 and hero_3:
            home.hero_images = [("image", hero_2), ("image", hero_3)]

        home.body = [
            ("nearest", {
                "heading": "Ближайшие выезды",
                "subheading": "Цены и свободные места — на текущую дату. "
                              "Обновляем каждое утро.",
                "limit": 6,
            }),
            ("manifest", {
                "numeral": "8",
                "eyebrow": "направлений",
                "heading": "Восемь мест, которые мы проверили лично",
                "body": (
                    "<p>Мы не продаём «туры на побережье вообще». У нас есть конкретные "
                    "точки: дикие пляжи между скалами, сосновый бор с дюнами, "
                    "плато с видом на долину и городская набережная.</p>"
                    "<p>Каждое направление проверяли лично и знаем, где там парковка, "
                    "где раздевалка, а где её нет вообще.</p>"
                ),
                "stats": [
                    {"value": "6 лет", "label": "возим каждую неделю"},
                    {"value": "1200+", "label": "довольных участников"},
                    {"value": "до 20", "label": "человек в группе"},
                ],
            }),
            ("grid", {
                "heading": "Куда едем",
                "subheading": "Восемь направлений, которые мы проверяли лично. Дикие пляжи, "
                              "сосновый бор, горы и набережная — без карамельных туров.",
                "featured_count": 1,
            }),
            ("steps", {
                "heading": "Как проходит поездка",
                "items": [
                    {"time": "6:00", "title": "Сбор группы",
                     "text": "Встречаемся в согласованной точке, грузимся и выезжаем."},
                    {"time": "8:30", "title": "В пути",
                     "text": "Песня, кофе, отвечаем на вопросы про еду и маршрут."},
                    {"time": "11:00", "title": "На месте",
                     "text": "Прибыли, разгрузились, первый час — свободный."},
                    {"time": "18:00", "title": "Обратный путь",
                     "text": "Собираемся и возвращаемся, никого не теряем."},
                    {"time": "21:00", "title": "Вы дома",
                     "text": "К этому времени каждый уже планирует следующий выезд."},
                ],
            }),
            ("quote", {
                "text": "Выходные — это не два дня дома. Это два дня, которые "
                        "разделены на «до» и «после».",
                "author": "Девиз клуба",
            }),
            ("faq", {
                "heading": "Частые вопросы",
                "items": [
                    {"question": "Нужен ли опыт поездок?",
                     "answer": "Нет. Первый раз едут больше половины наших участников. "
                               "Гид рядом, маршрут простой, группа небольшая."},
                    {"question": "Можно ли с детьми?",
                     "answer": "Да, для Ханской, Гиагинской, Дондуковской и Курганинска "
                               "мы специально выбирали места с мелкой и безопасной полосой."},
                    {"question": "Что взять с собой?",
                     "answer": "Купальник, полотенце, головной убор и наличные на парковку. "
                               "Полный список — на странице каждого направления."},
                    {"question": "Что если погода плохая?",
                     "answer": "Выезд переносим или возвращаем деньги. Решаем заранее, "
                               "не в день поездки."},
                    {"question": "Можно ли отменить?",
                     "answer": "Да. За 5 и более дней до выезда — полный возврат, "
                               "ближе к дате — уточняйте в мессенджере."},
                ],
            }),
            ("cta", {
                "heading": "Выходные ещё есть",
                "text": "Напишите, куда хотите поехать и когда. Скажем, сколько мест осталось.",
                "button_text": "Записаться",
            }),
        ]

        if not home.pk:
            root.add_child(instance=home)
            self.stdout.write("+ главная")
        else:
            self.stdout.write("~ главная пересобрана")
        home.save_revision().publish()
        return home

    def ensure_about(self, home):
        if AboutPage.objects.exists():
            return
        page = AboutPage(
            title="О клубе",
            slug="about",
            intro="Мы небольшая команда, которая каждую неделю собирает людей "
                  "и увозит их на побережье.",
            body=(
                "<p>«Нескучные выходные» — это поездки выходного дня по Краснодарскому "
                "краю и короткие туры с ночёвкой. Мы не работаем с пляжами по всему миру "
                "и не возим в другие страны: зато знаем каждое место, которое показываем.</p>"
                "<p>Формат простой: выезд в субботу утром, возвращение в тот же день "
                "вечером. Группа до 20 человек, автобус и сопровождающий. Если рядом "
                "живёте с детьми или без автомобиля — это ровно наш вариант.</p>"
                "<p>Списки формируем небольшими, чтобы не превращать поездку в поток "
                "людей на пляже. Если дата не набирается — переносим её или возвращаем "
                "взнос целиком.</p>"
            ),
            details=(
                "<p><strong>Реквизиты</strong><br>"
                "ИП Таможникова Наталия Александровна<br>"
                "ИНН 000000000000 · ОГРНИП 000000000000000</p>"
                "<p><strong>Как платить</strong><br>"
                "Оплата переводом на карту или наличными при посадке. "
                "Полный возврат при отмене за 5 и более дней до выезда.</p>"
            ),
            search_description="Клуб поездок выходного дня по Краснодарскому краю: "
                               "кто мы, как ездим и как вернуть деньги.",
        )
        page.figures = [
            ("figure", {"value": value, "label": label})
            for value, label in ABOUT_FIGURES
        ]
        home.add_child(instance=page)
        page.save_revision().publish()
        self.stdout.write("+ о клубе")

    def ensure_contact(self, home):
        if ContactPage.objects.exists():
            return
        page = ContactPage(
            title="Контакты",
            slug="contacts",
            body="Напишите, куда хотите поехать и в какие даты. Ответим в мессенджере "
                 "и заберём вас в группу.",
            phone="+7 900 000-00-00",
            email="outgoing@example.com",
            address="Краснодар и окрестности",
            work_hours="Ежедневно с 9:00 до 21:00",
            search_description="Контакты клуба «Нескучные выходные»: телефон, "
                               "мессенджеры и форма записи на поездку.",
        )
        home.add_child(instance=page)
        page.save_revision().publish()
        self.stdout.write("+ контакты")

    def ensure_info(self, home):
        if InfoPage.objects.exists():
            return
        page = InfoPage(
            title="Как добраться",
            slug="kak-dobratsya",
            body="Точки сбора и условия, о которых чаще всего спрашивают перед поездкой.",
        )
        page.meeting_points = [
            ("point", {
                "city": "Краснодар",
                "address": "ТЦ «Галерея», парковка у центрального входа",
                "time": "06:00",
                "note": "Собираемся у информационной стойки, автобус ждёт на парковке.",
            }),
            ("point", {
                "city": "Краснодар, Южный",
                "address": "Остановка «Южный», напротив торгового центра",
                "time": "06:10",
                "note": "Если едете из Южного — сюда, автобус делает остановку.",
            }),
            ("point", {
                "city": "Адыгейск",
                "address": "Центральная площадь, у памятника",
                "time": "05:40",
                "note": "Отдельная точка сбора для жителей Адыгейска и пригородов.",
            }),
        ]
        page.notes = [
            ("note", {
                "title": "Парковка",
                "text": "На большинстве пляжей парковка платная — 200–300 ₽. "
                        "В Гиагинской и Дондуковской бесплатная.",
            }),
            ("note", {
                "title": "Раздевалки и душ",
                "text": "Есть на Гиагинской. На диких пляжах душа нет — берите "
                        "полотенце и переодевайтесь в машине.",
            }),
            ("note", {
                "title": "Питание",
                "text": "В автобусе — вода. Обед не входит: на большинстве точек "
                        "кафе нет, уезжаем налегке.",
            }),
            ("note", {
                "title": "Wi-Fi и розетки",
                "text": "В автобусе ловит мобильный интернет. Розеток нет.",
            }),
        ]
        home.add_child(instance=page)
        page.save_revision().publish()
        self.stdout.write("+ как добраться")

    def ensure_legal(self, home):
        # Заглушка только на время первого запуска: полный комплект документов
        # (5 штук) приезжает командой import_ew_content из макета EWsite.
        pages = [
            (
                "offer",
                "Договор-оферта",
                "<p>Поездка считается забронированной после предоплаты и подтверждения "
                "с нашей стороны.</p>"
                "<p>Если на выезд не набирается группа, мы предлагаем перенос на другую "
                "дату или полный возврат.</p>"
                "<p>При отмене за 5 и более дней до выезда возвращаем всю сумму. "
                "При отмене менее чем за 2 дня удерживаем 30% — они уже потрачены "
                "на бронирование транспорта.</p>",
            ),
        ]
        for slug, title, body in pages:
            if LegalPage.objects.filter(slug=slug).exists():
                continue
            page = LegalPage(title=title, slug=slug, body=body)
            home.add_child(instance=page)
            page.save_revision().publish()
            self.stdout.write(f"+ {title.lower()}")

    def ensure_groups(self):
        for name, perms in [
            ("Редактор", ["view", "change"]),
            ("Администратор", ["view", "change", "add", "delete"]),
        ]:
            group, created = Group.objects.get_or_create(name=name)
            self.stdout.write(f"{'+' if created else '='} группа «{name}»")

    # ── направления и выезды ───────────────────────────────────
    def ensure_destinations(self, index) -> list:
        created = []
        for data in DESTINATIONS:
            existing = Destination.objects.filter(slug=data["slug"]).first()
            if existing:
                created.append(existing)
                continue

            slug = data["slug"]
            cover = self.make_image(slug, f"{data['title']} — обложка", "card",
                                    "placeholder-card-4x3-1200x900.webp")
            hero_1 = self.make_image(slug, f"{data['title']} — первый экран", "hero",
                                     "placeholder-hero-wide-2400x1400.webp")
            hero_2 = self.make_image(slug, f"{data['title']} — галерея 1", "card",
                                     "placeholder-card-4x3-1200x900.webp")
            hero_3 = self.make_image(slug, f"{data['title']} — галерея 2", "card",
                                     "placeholder-card-4x3-1200x900.webp")

            page = Destination(
                title=data["title"],
                slug=slug,
                subtitle=data["subtitle"],
                kind=data["kind"],
                eyebrow=data["eyebrow"],
                cover=cover,
                price_from=data["price_from"],
                duration=data["duration"],
                distance=data["distance"],
                travel_time=data["travel_time"],
                parking=data["parking"],
                summary=data["summary"],
                description=data["description"],
                search_description=(
                    f"{data['title']} — {data['subtitle'].lower()}. "
                    f"{data['distance']}, {data['travel_time']} в пути. "
                    f"Поездка от {data['price_from']} ₽."
                ),
                show_in_menus=True,
            )

            # Списки-«галочки» хранятся как StreamField с одним ListBlock
            def bullets(items):
                return [("items", [{"value": item} for item in items])]

            page.highlights = bullets(data["highlights"])
            page.included = bullets(data["included"])
            page.excluded = bullets(data["excluded"])
            page.packing = bullets(data["packing"])

            hero_stream = [
                ("image", img) for img in (hero_1, hero_2, hero_3) if img
            ]
            if hero_stream:
                page.gallery_hero = hero_stream
            if cover:
                page.gallery = [("image", cover)]

            index.add_child(instance=page)
            page.save_revision().publish()
            created.append(page)
            self.stdout.write(f"+ направление «{data['title']}»")

        return created

    def ensure_departures(self, destinations: list) -> int:
        """Выезды на 12 недель вперёд: пятница, суббота и воскресенье."""
        total = 0
        for page in destinations:
            if page.departures.exists():
                total += page.departures.count()
                continue

            base_price = int(page.price_from.replace(" ", "") or 1900)
            start = date.today()
            # ближайшая пятница
            days_to_friday = (4 - start.weekday()) % 7
            first = start + timedelta(days=days_to_friday)

            for week in range(12):
                for weekday in (4, 5, 6):
                    day = first + timedelta(days=week * 7 + (weekday - 4))
                    # «мало мест» — чтобы в интерфейсе было видно бейдж
                    seats_total = 20
                    if week == 0 and weekday == 4:
                        seats_left = 3
                    elif week == 1 and weekday == 5:
                        seats_left = 5
                    else:
                        seats_left = seats_total

                    Departure.objects.create(
                        destination=page,
                        start_date=day,
                        price=base_price + (week % 3) * 100,
                        seats_total=seats_total,
                        seats_left=seats_left,
                        meeting_point="ТЦ «Галерея», парковка у центрального входа",
                        meeting_time=time(6, 0),
                        status=Departure.Status.PLANNED,
                        price_note="при бронировании за 3 дня −10%" if week % 4 == 0 else "",
                    )
                    total += 1

            self.stdout.write(f"  · {page.title}: 36 выездов")
        return total