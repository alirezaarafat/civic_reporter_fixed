from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Areas"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Report(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        VERIFIED = "verified", "Verified"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=5000)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="reports")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="reports")
    location = models.CharField(max_length=255, help_text="Street, landmark, or precise public location")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    photo = models.ImageField(upload_to="report_photos/", null=True, blank=True)
    resolution_photo = models.ImageField(upload_to="resolution_photos/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.title}"


class StatusHistory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="status_history")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="report_status_changes")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, choices=Report.Status.choices)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Verification(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="verifications")
    verifier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verifications")
    is_valid = models.BooleanField()
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["report", "verifier"], name="unique_report_verifier")]


class Comment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_comments")
    body = models.CharField(max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Upvote(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="upvotes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_upvotes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["report", "user"], name="unique_report_upvote")]


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
