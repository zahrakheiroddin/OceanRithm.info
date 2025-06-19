from django.contrib import admin
from .models import GitHubConfig, Repository

@admin.register(GitHubConfig)
class GitHubConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'github_username', 'noreply_email')
    search_fields = ('user__username', 'github_username')

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'url', 'created_at', 'is_private')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'user__username', 'description') 