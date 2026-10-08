from django.db import migrations


def disable_workflows(apps, schema_editor):
    """Гасим все workflow: кнопка «Отправить в модерацию» больше не нужна.

    Сделано миграцией, а не правкой базы руками, чтобы состояние
    одинаково было у разработки и на хостинге.
    """
    Workflow = apps.get_model("wagtailcore", "Workflow")
    Workflow.objects.update(active=False)


def enable_workflows(apps, schema_editor):
    Workflow = apps.get_model("wagtailcore", "Workflow")
    Workflow.objects.update(active=True)


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0008_remove_destination_distance_km_and_more"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [
        migrations.RunPython(disable_workflows, enable_workflows),
    ]
