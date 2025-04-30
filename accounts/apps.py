from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Admin Portal'

    def ready(self):
        """
        Import signals when the app is ready
        """
        # Import signals to register them
        # import accounts.signals
