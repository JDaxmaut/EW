"""Убирает лишнюю обёртку {"value": ...} в списках маршрутов.

Поля highlights / included / excluded / packing — это StreamField с
единственным блоком "items", внутри которого ListBlock(CharBlock).
CharBlock хранит просто строку, но данные были записаны как
{"value": "строка"}. Публичный шаблон такую форму терпел, а форма в
админке показывала редактору "{'value': 'Бухта на 30 шагов…'}".

Миграция приводит значения к тому, что ListBlock ожидает на самом деле.
"""
import json

from django.db import migrations

FIELDS = ["highlights", "included", "excluded", "packing"]
TABLE = "trips_destination"
PK = "page_ptr_id"


def unwrap(value):
    """Если значение — {"value": X}, вернуть X. Иначе не трогать."""
    if isinstance(value, dict) and set(value.keys()) == {"value"}:
        return value["value"]
    return value


def fix_stream(raw):
    """Починить один JSON StreamField. Возвращает новый JSON или None."""
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None

    changed = False

    def walk(node):
        nonlocal changed
        if isinstance(node, dict):
            if node.get("type") == "item" and isinstance(node.get("value"), dict):
                new_value = unwrap(node["value"])
                if new_value is not node["value"]:
                    node["value"] = new_value
                    changed = True
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    if not changed:
        return None
    return json.dumps(data, ensure_ascii=False)


def fix_lists(apps, schema_editor):
    quote = schema_editor.connection.ops.quote_name
    table = quote(TABLE)
    pk = quote(PK)
    columns = ", ".join(quote(f) for f in FIELDS)

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT {pk}, {columns} FROM {table}")
        rows = cursor.fetchall()

        fixed_rows = 0
        for row in rows:
            new_values = [fix_stream(value) for value in row[1:]]
            if not any(new_values):
                continue
            assignments = ", ".join(
                f"{quote(field)} = %s"
                for field, value in zip(FIELDS, new_values)
                if value is not None
            )
            params = [v for v in new_values if v is not None] + [row[0]]
            cursor.execute(f"UPDATE {table} SET {assignments} WHERE {pk} = %s", params)
            fixed_rows += 1

    print(f"  починено строк: {fixed_rows}")


def unfix_lists(apps, schema_editor):
    """Обратное преобразование невозможно однозначно — ничего не делаем."""


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0009_disable_moderation_workflows"),
    ]

    operations = [
        migrations.RunPython(fix_lists, unfix_lists),
    ]
