from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Client Portal'

    def ready(self):
        """
        Import signals when the app is ready
        """
        # Import signals to register them
        # import users.signals
