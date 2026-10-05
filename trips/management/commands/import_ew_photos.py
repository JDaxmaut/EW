"""
Импорт фотографий из макета EWsite в библиотеку Wagtail.

    python manage.py import_ew_photos
    python manage.py import_ew_photos --force

Что делает:
  1. Берёт готовые кадры из static/img/ew (hero, обложки направлений, стена).
  2. Создаёт по ним объекты Wagtail Images (WebP, с размерами).
  3. Раскладывает их по страницам: обложка направления, галерея, фото главной.

Зачем: менеджер должен видеть в админке те же кадры, что и на сайте, и мог
заменить их на реальные одним перетаскиванием.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from PIL import Image as PILImage
from wagtail.images import get_image_model

from trips.models import Destination, HomePage


class Command(BaseCommand):
    help = "Импортирует фото из static/img/ew в библиотеку Wagtail"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="пересоздать объекты")

    def handle(self, *args, **options):
        src = Path(settings.BASE_DIR) / "static" / "img" / "ew"
        if not src.exists():
            self.stderr.write(f"Нет папки {src}")
            return

        Image = get_image_model()
        created = 0

        # ── фото главной ──────────────────────────────────────────
        hero = self.import_file(Image, src / "hero-stock.webp", "Главная — первый экран",
                                options["force"])
        created += bool(hero)
        extra = [
            self.import_file(Image, src / "wall-aerial.webp", "Стена — аэросъёмка", options["force"]),
            self.import_file(Image, src / "wall-waves.webp", "Стена — вода", options["force"]),
        ]
        extra = [i for i in extra if i]

        home = HomePage.objects.first()
        if home and hero:
            home.hero_image = hero
            home.hero_images = [("image", img) for img in extra]
            home.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("+ первый экран главной"))

        # ── обложки направлений ──────────────────────────────────
        for destination in Destination.objects.all():
            slug = destination.slug
            cover_file = src / f"dest-{slug}.webp"
            if not cover_file.exists():
                continue
            cover = self.import_file(
                Image, cover_file, f"{destination.title} — обложка", options["force"]
            )
            created += bool(cover)
            if cover:
                destination.cover = cover
                destination.gallery = [("image", cover)]
                destination.save_revision().publish()
                self.stdout.write(self.style.SUCCESS(f"+ обложка «{destination.title}»"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Готово. Создано изображений: {created}"))

    def import_file(self, Image, path: Path, title: str, force: bool):
        if not path.exists():
            return None
        existing = Image.objects.filter(title=title).first()
        if existing and not force:
            return existing
        if existing and force:
            existing.delete()

        with PILImage.open(path) as probe:
            width, height = probe.size
        with open(path, "rb") as fh:
            return Image.objects.create(
                title=title,
                file=File(fh, name=path.name),
                width=width,
                height=height,
            )