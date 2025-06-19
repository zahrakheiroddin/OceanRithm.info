from django.apps import AppConfig

# github actions app
class RepositoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'githubaction'
    
    def ready(self):
        import githubaction.signals  # Import signals 