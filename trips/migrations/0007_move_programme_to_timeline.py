"""Переносит почасовую программу из «дней» в линию времени.

Старые блоки хранили время вперемешку с названием («6:00 - Сбор и отправление»).
Разбираем время обратно в отдельное поле, чтобы редактору не приходилось
переписывать программу руками. Данные не теряются: исходный текст сохраняется.
"""

from django.db import migrations

import json


def read_blocks(field):
    """Читает StreamField независимо от того, строка это или RawDataView."""
    raw = field.raw_data
    if not raw:
        return []
    if isinstance(raw, (str, bytes, bytearray)):
        return json.loads(raw)
    return list(raw)


def split_time(title):
    """«6:00 - Сбор и отправление» -> («6:00», «Сбор и отправление»)."""
    for separator in (" - ", " – ", " — ", "-", "–", "—"):
        if separator in title:
            head, _, tail = title.partition(separator)
            head, tail = head.strip(), tail.strip()
            if head and tail:
                return head, tail
    return "", title.strip()


def forwards(apps, schema_editor):
    Destination = apps.get_model("trips", "Destination")

    for destination in Destination.objects.all():
        if destination.timeline:
            continue

        days = read_blocks(destination.programme)
        if not days:
            # Ночёвочный формат ставим по наличию мест ночёвки.
            if destination.stay and destination.stay.raw_data:
                destination.format = "overnight"
                destination.save(update_fields=["format"])
            continue

        steps = []
        for block in days:
            if block.get("type") != "day":
                continue
            value = block.get("value", {})
            time, title = split_time(value.get("title", ""))
            steps.append(
                {
                    "type": "step",
                    "value": {
                        "time": time,
                        "title": title,
                        "text": value.get("text", ""),
                        "image": value.get("image"),
                    },
                }
            )

        if not steps:
            continue

        destination.timeline = steps
        destination.save(update_fields=["timeline"])


def backwards(apps, schema_editor):
    """Возвращает шаги обратно в дневные блоки, склеивая время с названием."""
    Destination = apps.get_model("trips", "Destination")

    for destination in Destination.objects.all():
        steps = read_blocks(destination.timeline)
        if not steps:
            continue

        days = []
        for block in steps:
            if block.get("type") != "step":
                continue
            value = block.get("value", {})
            time, title = value.get("time", ""), value.get("title", "")
            days.append(
                {
                    "type": "day",
                    "value": {
                        "day_number": len(days) + 1,
                        "title": f"{time} - {title}" if time else title,
                        "text": value.get("text", ""),
                        "image": value.get("image"),
                    },
                }
            )

        if not days:
            continue

        destination.programme = days
        destination.save(update_fields=["programme"])


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0006_destination_format_destination_timeline_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
