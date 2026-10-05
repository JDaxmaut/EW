"""
Загрузка фотографий со стоков.

    python manage.py fetch_stock_photos
    python manage.py fetch_stock_photos --only hanskaya dondukovskaya
    python manage.py fetch_stock_photos --provider wikimedia

Что делает:
  1. По каждому направлению ищет изображения через Openverse API
     (без ключей, только CC-лицензии) и, если он недоступен, через
     Wikimedia Commons API.
  2. Скачивает файлы в media/stock/<slug>-<слот>.jpg.
  3. Пишет media/stock/sources.json — источник, автор, лицензия, дата.
     Это обязательный шаг: без атрибуции фото нельзя использовать на сайте.

Слоты под каждый набор: hero (16:9), card (4:3), square (1:1).

Если сеть недоступна — команда не падает, а честно пишет, что ничего не скачала.
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image

# Поисковые запросы под каждое направление. Общие, без привязки к брендам.
QUERIES = {
    "home": {
        "hero": "sea beach coastline",
        "card": "sea horizon beach morning light",
        "square": "pines by the sea coast",
    },
    "hanskaya": {
        "hero": "wild pebble beach cliffs sea anapa",
        "card": "black sand beach cliffs turquoise sea",
        "square": "rocky coastline empty beach",
    },
    "dondukovskaya": {
        "hero": "pine forest coastline dunes sea",
        "card": "empty beach dunes pine trees",
        "square": "coastal pine forest beach",
    },
    "giaginskaya": {
        "hero": "wide shallow sandy beach turquoise water",
        "card": "shallow sea sandy beach family holiday",
        "square": "clear shallow water beach sand",
    },
    "labinsk": {
        "hero": "river embankment town promenade summer",
        "card": "city river embankment walk",
        "square": "riverside promenade town",
    },
    "maykop": {
        "hero": "mountain plateau canyon green pine",
        "card": "caucasus mountains green valley",
        "square": "mountain viewpoint forest",
    },
    "belorechensk": {
        "hero": "mountain gorge green river limestone",
        "card": "mountain cave entrance forest",
        "square": "green gorge rocky river",
    },
    "kurgansk": {
        "hero": "quiet pebble beach calm sea",
        "card": "calm sea horizon beach shells",
        "square": "pebble beach water",
    },
    "krasnodar": {
        "hero": "city embankment summer evening lights",
        "card": "city park summer people walking",
        "square": "city street summer",
    },
}

SLOT_SIZES = {
    "hero": (1920, 1080),
    "card": (1200, 900),
    "square": (900, 900),
}

USER_AGENT = "NeskuchnyeVyhodnye/1.0 (site build; contact: outgoing@example.com)"

# Wikimedia возвращает гравюры, карты и рисунки XIX века — на сайте им не место.
BAD_TITLE_WORDS = (
    # гравюры, карты, рисунки
    "engrav", "lithograph", "etching", "sketch", "painting", "drawing",
    "woodcut", "print", "plate", "map", "chart", "diagram", "illustration",
    "illustrated", "delineation", "pen and pencil", "icon ", "portrait of",
    # старые книги и журналы — их много в выдаче, и они не похожи на фото
    "pacific tourist", "picturesque", "journal", "proceedings", "bulletin",
    "annual report", "guide of travel", "trans-continental", "proceedings",
    "quarterly", "monthly", "annual", "volume ", "book", "page ",
    "postcard", "cover of", "title page", "frontispiece",
)

# Файл из книги 1890 года — это не фотография. Отсекаем по году в названии.
OLD_YEAR = re.compile(r"\b(1[0-9]{3})\b")
MIN_YEAR = 1950


def looks_like_old_paper(title: str) -> bool:
    match = OLD_YEAR.search(title)
    return bool(match and int(match.group(1)) < MIN_YEAR)

MIN_WIDTH = 1400
MIN_HEIGHT = 900


class Command(BaseCommand):
    help = "Скачивает фотографии со свободных лицензий в media/stock"

    def add_arguments(self, parser):
        parser.add_argument("--only", nargs="*", help="только эти slug-и")
        parser.add_argument(
            "--provider", default="openverse", choices=["openverse", "wikimedia"]
        )
        parser.add_argument("--per-slot", type=int, default=3, help="кандидатов на слот")
        parser.add_argument("--timeout", type=int, default=20)
        parser.add_argument("--force", action="store_true")

    # ── HTTP ───────────────────────────────────────────────────
    def fetch_json(self, url: str, timeout: int):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as err:
            self.stderr.write(f"  ! {type(err).__name__}: {err}")
            return None

    def search_openverse(self, query: str, limit: int, timeout: int):
        params = urllib.parse.urlencode(
            {
                "q": query,
                "page_size": max(limit * 4, 12),
                # Только лицензии, пригодные для коммерческого сайта:
                # CC0 / Public Domain / CC BY / CC BY-SA.
                # CC BY-NC и CC BY-ND исключены — клиент живёт на выездах за деньги.
                "license": "cc0,pdm,by,by-sa",
                "mature": "false",
            }
        )
        data = self.fetch_json(f"https://api.openverse.org/v1/images/?{params}", timeout)
        if not data:
            return []
        results = []
        for item in data.get("results", []):
            url = item.get("url")
            if not url:
                continue
            results.append(
                {
                    "url": url,
                    "title": item.get("title") or query,
                    "creator": item.get("creator") or "",
                    "license": f"CC {(item.get('license') or '').upper()} {item.get('license_version') or ''}".strip(),
                    "source": item.get("source") or "openverse",
                    "page": item.get("foreign_landing_url") or url,
                }
            )
        return results

    def search_wikimedia(self, query: str, limit: int, timeout: int):
        params = urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": "6",
                "gsrlimit": max(limit * 3, 10),
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": "1920",
            }
        )
        data = self.fetch_json(f"https://commons.wikimedia.org/w/api.php?{params}", timeout)
        if not data:
            return []
        pages = (data.get("query") or {}).get("pages") or {}
        results = []
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            url = info.get("thumburl") or info.get("url")
            if not url:
                continue

            title = page.get("title", "")
            low = title.lower()
            if any(word in low for word in BAD_TITLE_WORDS):
                continue
            if looks_like_old_paper(title):
                continue
            mime = info.get("mime", "")
            if mime and mime not in ("image/jpeg", "image/png"):
                continue
            if info.get("thumbwidth", 0) and info["thumbwidth"] < MIN_WIDTH:
                continue
            meta = info.get("extmetadata") or {}

            def field(name):
                return (meta.get(name) or {}).get("value", "")

            results.append(
                {
                    "url": url,
                    "title": title,
                    "creator": field("Artist")[:200],
                    "license": (field("LicenseShortName") or "CC").strip(),
                    "source": "wikimedia",
                    "page": info.get("descriptionurl") or url,
                }
            )
        return results

    def download(self, url: str, target: Path, timeout: int):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        if len(data) < 20_000:  # явно не фотография
            return False
        target.write_bytes(data)
        return True

    @staticmethod
    def signature(path: Path, grid: int = 8):
        """Грубая сигнатура кадра: сетка средних цветов.

        Нужна, чтобы не поставить в коллаж три почти одинаковых пляжа —
        на скриншоте это сразу бросается в глаза.
        """
        with Image.open(path) as image:
            small = image.convert("L").resize((grid, grid), Image.LANCZOS)
            pixels = list(small.getdata())
        return sum(pixels) / len(pixels), pixels

    @classmethod
    def too_similar(cls, signature, taken):
        if not taken:
            return False
        mean, pixels = signature
        for other in taken:
            if abs(mean - other[0]) < 4:
                diff = sum(abs(a - b) for a, b in zip(pixels, other[1])) / len(pixels)
                if diff < 6:
                    return True
        return False

    def crop_to_slot(self, path: Path, slot: str, target: Path):
        """Приводим скачанный файл к пропорциям слота и пережимаем в WebP."""
        width, height = SLOT_SIZES[slot]
        with Image.open(path) as image:
            image = image.convert("RGB")
            target_ratio = width / height
            source_ratio = image.width / image.height

            if source_ratio > target_ratio:  # обрезаем по бокам
                new_width = int(image.height * target_ratio)
                left = (image.width - new_width) // 2
                image = image.crop((left, 0, left + new_width, image.height))
            else:  # обрезаем сверху и снизу, верх чуть важнее
                new_height = int(image.width / target_ratio)
                top = int((image.height - new_height) * 0.35)
                image = image.crop((0, top, image.width, top + new_height))

            image = image.resize((width, height), Image.LANCZOS)
            image.save(target, "WEBP", quality=84)
            path.unlink(missing_ok=True)
        return target

    # ── основной проход ───────────────────────────────────────
    def handle(self, *args, **options):
        stock_dir = Path(settings.MEDIA_ROOT) / "stock"
        stock_dir.mkdir(parents=True, exist_ok=True)
        sources_file = stock_dir / "sources.json"

        sources = {}
        if sources_file.exists():
            sources = json.loads(sources_file.read_text(encoding="utf-8"))

        slugs = options["only"] or list(QUERIES.keys())
        searcher = (
            self.search_openverse
            if options["provider"] == "openverse"
            else self.search_wikimedia
        )

        # сигнатуры уже скачанных файлов — чтобы не плодить дубли
        taken = []
        for existing in sorted(stock_dir.glob("*.webp")):
            taken.append(self.signature(existing))

        downloaded = 0
        for slug in slugs:
            slots = QUERIES.get(slug)
            if not slots:
                self.stderr.write(f"Нет запросов для «{slug}»")
                continue

            for slot, query in slots.items():
                target = stock_dir / f"{slug}-{slot}.webp"
                if target.exists() and not options["force"]:
                    self.stdout.write(f"— {target.name} уже есть")
                    continue

                candidates = searcher(query, options["per_slot"], options["timeout"])
                if not candidates:
                    self.stderr.write(
                        f"  {slug}/{slot}: ничего не нашлось (проверьте интернет)"
                    )
                    continue

                saved = False
                for candidate in candidates:
                    known_urls = {v["url"] for v in sources.values()}
                    known_titles = {v["title"] for v in sources.values()}
                    if candidate["url"] in known_urls or candidate["title"] in known_titles:
                        # тот же снимок уже стоит на другой странице —
                        # повторять его в коллаже нельзя
                        continue
                    raw = stock_dir / f"_tmp-{slug}-{slot}.jpg"
                    try:
                        if not self.download(candidate["url"], raw, options["timeout"]):
                            continue
                        result = self.crop_to_slot(raw, slot, target)
                        if self.too_similar(self.signature(result), taken):
                            result.unlink(missing_ok=True)
                            continue  # похож на уже скачанный — берём следующий
                    except Exception as err:  # noqa: BLE001 — сеть отдаёт что угодно
                        self.stderr.write(f"  ! {candidate['url'][:60]}: {err}")
                        continue
                    finally:
                        raw.unlink(missing_ok=True)

                    taken.append(self.signature(result))

                    sources[str(result.relative_to(Path(settings.MEDIA_ROOT)))] = {
                        **candidate,
                        "downloaded": str(date.today()),
                        "slot": slot,
                        "destination": slug,
                    }
                    self.stdout.write(self.style.SUCCESS(f"+ {result.name}"))
                    downloaded += 1
                    saved = True
                    break

                if not saved:
                    self.stderr.write(f"  {slug}/{slot}: не удалось скачать ни одного файла")
                time.sleep(0.4)  # не долбим API

        sources_file.write_text(
            json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Скачано файлов: {downloaded}. Атрибуция — {sources_file}"
            )
        )
        if downloaded == 0:
            self.stdout.write(
                "Ничего не скачалось: скорее всего, нет доступа в интернет. "
                "На сайте останутся бирюзовые плейсхолдеры — это не поломка."
            )