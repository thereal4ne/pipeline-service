from django.contrib import admin
from .models import UserProfile, Project, Build, BuildLog, DeployTarget


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('github_username', 'github_id', 'user')
    search_fields = ('github_username',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('repo_full_name', 'owner', 'detected_framework', 'created_at')
    search_fields = ('repo_full_name',)
    list_filter = ('detected_framework',)


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'commit_sha', 'trigger_author', 'created_at')
    search_fields = ('commit_sha', 'trigger_author')
    list_filter = ('status',)


@admin.register(BuildLog)
class BuildLogAdmin(admin.ModelAdmin):
    list_display = ('build', 'timestamp')
    search_fields = ('log_text',)


@admin.register(DeployTarget)
class DeployTargetAdmin(admin.ModelAdmin):
    list_display = ('project', 'provider', 'is_active')
    list_filter = ('provider', 'is_active')
