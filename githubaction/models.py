from django.db import models
from django.contrib.auth.models import User

class GitHubConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    github_token = models.CharField(max_length=255)
    github_username = models.CharField(max_length=255)
    noreply_email = models.EmailField()
    
    def __str__(self):
        return f"{self.user.username}'s GitHub Config"
    
    def save(self, *args, **kwargs):
        # Auto-generate noreply email if not provided
        if not self.noreply_email and self.github_username:
            self.noreply_email = f"{self.github_username}@users.noreply.github.com"
        super().save(*args, **kwargs)

class Repository(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    url = models.URLField()
    local_path = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name 