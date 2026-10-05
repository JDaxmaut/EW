"""
Генератор плейсхолдеров: бирюзовые плашки под каждый фотографический слот.

Зачем: сайт не должен выглядеть сломанным, пока клиент не загрузил фотографии.
Плашка сразу показывает, ЧТО сюда вставлять (пропорции и подпись).

    python manage.py placeholders
    python manage.py placeholders --width 1200 --height 900
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TURQUOISE = (0, 194, 176)
MINT_300 = (111, 227, 214)
INK = (6, 61, 58)


def _font(size: int):
    """Шрифт покрупнее из системных, без внешних зависимостей."""
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _gradient(width: int, height: int, top=TURQUOISE, bottom=MINT_300) -> Image.Image:
    """Вертикальный градиент: рисуем построчно, дешевле и без швов."""
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    return image


def _soft_shapes(image: Image.Image) -> Image.Image:
    """Пара размытых окружностей — чтобы плейсхолдер не был плоской заливкой."""
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    w, h = image.size
    draw.ellipse([w * 0.55, -h * 0.25, w * 1.35, h * 0.65], fill=(255, 255, 255, 60))
    draw.ellipse([-w * 0.2, h * 0.45, w * 0.5, h * 1.35], fill=(6, 61, 58, 45))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(w, h) // 14))
    image = image.convert("RGBA")
    image.alpha_composite(layer)
    return image.convert("RGB")


def _caption(image: Image.Image, title: str, note: str = "") -> Image.Image:
    draw = ImageDraw.Draw(image)
    w, h = image.size
    unit = min(w, h) / 900

    title_font = _font(max(16, int(30 * unit)))
    note_font = _font(max(11, int(15 * unit)))

    if title:
        box = draw.textbbox((0, 0), title, font=title_font)
        draw.text(((w - (box[2] - box[0])) / 2, h / 2 - 26 * unit), title,
                  font=title_font, fill=INK)
    if note:
        box = draw.textbbox((0, 0), note, font=note_font)
        draw.text(((w - (box[2] - box[0])) / 2, h / 2 + 14 * unit), note,
                  font=note_font, fill=INK)

    # подпись снизу: какую пропорцию заменить
    size_note = f"{w}×{h} — заменить на фото"
    box = draw.textbbox((0, 0), size_note, font=note_font)
    draw.text(((w - (box[2] - box[0])) / 2, h - 34 * unit), size_note,
              font=note_font, fill=INK)

    return image


class Command(BaseCommand):
    help = "Создаёт бирюзовые плейсхолдеры для всех фотографических слотов"

    SLOTS = [
        ("hero-wide", 2400, 1400, "Первый экран", "2400×1400 — широкий кадр с морем"),
        ("hero-1", 1200, 1400, "Коллаж 1", "1200×1400 — вертикальный кадр"),
        ("hero-2", 800, 600, "Коллаж 2", "800×600 — кадр в коллаж"),
        ("hero-3", 800, 1000, "Коллаж 3", "800×1000 — кадр в коллаж"),
        ("card-4x3", 1200, 900, "Карточка", "1200×900 — 4:3, обложка направления"),
        ("tile-3x4", 900, 1200, "Плитка", "900×1200 — 3:4 для bento"),
        ("gallery-1", 720, 540, "Галерея", "720×540 — первый кадр мозаики"),
        ("wall-square", 800, 800, "Фото-стена", "800×800 — квадрат для стены"),
    ]

    def add_arguments(self, parser):
        parser.add_argument("--out", default=None, help="куда класть файлы")
        parser.add_argument("--force", action="store_true", help="перезаписать существующие")

    def handle(self, *args, **options):
        out_dir = Path(options["out"] or (Path(settings.MEDIA_ROOT) / "placeholders"))
        out_dir.mkdir(parents=True, exist_ok=True)

        for name, width, height, title, note in self.SLOTS:
            path = out_dir / f"placeholder-{name}-{width}x{height}.webp"
            if path.exists() and not options["force"]:
                self.stdout.write(f"— {path.name} уже есть")
                continue

            image = _gradient(width, height)
            image = _soft_shapes(image)
            image = _caption(image, title, note)
            image.save(path, "WEBP", quality=86)

            self.stdout.write(self.style.SUCCESS(f"+ {path.name}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nГотово: {len(self.SLOTS)} плейсхолдеров в {out_dir}")
        )