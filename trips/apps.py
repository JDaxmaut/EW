from django.apps import AppConfig
from django.db.backends.signals import connection_created


class TripsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trips"
    verbose_name = "Поездки"

    def ready(self):
        def set_wal(sender, connection, **kwargs):
            if connection.vendor == "sqlite":
                with connection.cursor() as cursor:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")

        connection_created.connect(set_wal)