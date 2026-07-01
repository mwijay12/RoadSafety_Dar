from django.apps import AppConfig


class AccidentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accidents"
    verbose_name = "Road Accident Records"

    def ready(self):
        import accidents.signals  # noqa: F401
