from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'
    verbose_name = 'События и заявки'

    def ready(self):
        # Регистрируем сигнал автосоздания Dialog/Message при создании Application
        from . import signals  # noqa: F401
