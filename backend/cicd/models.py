import uuid
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    # Link to Django's built-in User table.
    # on_delete=models.CASCADE means if the User is deleted, delete this profile too.
    # related_name='profile' lets us write: user.profile in Python to get these extra fields.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Store GitHub numeric ID (e.g., 98765432)
    github_id = models.BigIntegerField(unique=True, null=True, blank=True)

    # Store GitHub handle (e.g., 'octocat')
    github_username = models.CharField(max_length=150, blank=True)

    # Store link to their profile picture
    avatar_url = models.URLField(max_length=500, blank=True)

    # Store the GitHub OAuth access token (encrypted for security)
    access_token_encrypted = models.TextField(blank=True)

    def __str__(self):
        # Tells Django how to display this object as a string in logs/admin panel
        return f"{self.github_username or self.user.username}"


class Project(models.Model):
    # 1. Primary Key: Using a random UUID instead of sequential integer IDs (1, 2, 3)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 2. Owner: Links this Project to the User who connected it.
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    # 3. Repository names
    repo_name = models.CharField(max_length=255)
    repo_full_name = models.CharField(max_length=255, unique=True)
    default_branch = models.CharField(max_length=100, default='main')

    # 4. Pipeline Config (commands to run inside Docker container)
    detected_framework = models.CharField(max_length=100, default='unknown')
    build_command = models.TextField(blank=True, default='')
    test_command = models.TextField(blank=True, default='')
    deploy_command = models.TextField(blank=True, default='')

    # 5. Security Secret: Unique secret generated per project to verify GitHub push webhooks via HMAC-SHA256
    webhook_secret = models.CharField(max_length=255, default=uuid.uuid4)

    # 6. Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.repo_full_name


class Build(models.Model):
    class BuildStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ForeignKey links this build to its parent Project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='builds')

    # Status of the build (starts as PENDING, updates to RUNNING -> SUCCESS/FAILED)
    status = models.CharField(max_length=20, choices=BuildStatus.choices, default=BuildStatus.PENDING)

    # Git commit details from GitHub Webhook payload
    commit_sha = models.CharField(max_length=40)
    commit_message = models.TextField(blank=True)
    trigger_author = models.CharField(max_length=150, blank=True)

    # Execution metrics
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.repo_name} - {self.commit_sha[:7]} ({self.status})"


class BuildLog(models.Model):
    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name='logs')
    log_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Log for Build {self.build.id} at {self.timestamp}"


class DeployTarget(models.Model):
    class Provider(models.TextChoices):
        RENDER = 'RENDER', 'Render'
        RAILWAY = 'RAILWAY', 'Railway'
        CUSTOM_WEBHOOK = 'CUSTOM_WEBHOOK', 'Custom Webhook'

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='deploy_target')
    provider = models.CharField(max_length=50, choices=Provider.choices, default=Provider.RENDER)
    deploy_url = models.URLField(max_length=500, blank=True)

    # Secret API key encrypted at rest
    api_token_encrypted = models.TextField(blank=True, help_text="Fernet encrypted deploy API token")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.provider} deployment for {self.project.repo_name}"
