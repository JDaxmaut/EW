"""Убрать с двух направлений цветные заглушки, поставленные вместо фотографий.

Зачем: у туров «Гуамка» и «Ейск» настоящих фотографий нет — стояли
плоские цветные картинки, и карточка тура выглядела как готовая, хотя
смотреть было не на что. Заглушки убрали, чтобы редактор увидел пустое
поле и загрузил настоящее фото.

Важно: правим не «все обложки этих туров», а только файлы-заглушки с
именами dest-guama* и dest-yeisk*. Если редактор позже поставит туру
настоящее фото (с другим именем файла), миграция его не тронет.
"""
from pathlib import Path

from django.db import migrations

# slug тура -> начало имени файла-заглушки
PLACEHOLDER_PREFIXES = {
    "guama": "dest-guama",
    "yeisk": "dest-yeisk",
}


def _is_placeholder(image, prefix):
    name = getattr(getattr(image, "file", None), "name", "") or ""
    return Path(name).name.startswith(prefix)


def clear_placeholder_covers(apps, schema_editor):
    Destination = apps.get_model("trips", "Destination")

    for slug, prefix in PLACEHOLDER_PREFIXES.items():
        changed = 0
        for page in Destination.objects.filter(slug=slug, cover__isnull=False):
            if _is_placeholder(page.cover, prefix):
                page.cover = None
                page.save(update_fields=["cover"])
                changed += 1
        if changed:
            print(f"  {slug}: снято заглушек — {changed}")


def restore_placeholder_covers(apps, schema_editor):
    """Вернуть заглушку обратно, только если такой файл ещё есть в медиа.

    Иначе откат приводил бы страницу в нерабочее состояние: карточка
    ссылалась бы на несуществующую картинку.
    """
    Destination = apps.get_model("trips", "Destination")
    wagtailimages = apps.get_model("wagtailimages", "Image")

    for slug, prefix in PLACEHOLDER_PREFIXES.items():
        image = None
        for candidate in wagtailimages.objects.filter(file__startswith="original_images/"):
            if Path(candidate.file.name).name.startswith(prefix):
                image = candidate
                break
        if image is None:
            print(f"  {slug}: заглушка не найдена в медиа, пропускаем")
            continue
        Destination.objects.filter(slug=slug, cover__isnull=True).update(cover=image)
        print(f"  {slug}: заглушка возвращена")


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0010_fix_bullet_lists"),
    ]

    operations = [
        migrations.RunPython(clear_placeholder_covers, restore_placeholder_covers),
    ]