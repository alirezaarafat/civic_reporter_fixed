from django.contrib import admin
from .models import Area, Category, Report, StatusHistory, Verification, Comment, Upvote, Notification

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ["name", "location"]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name", "type"]

class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ["changed_by", "old_status", "new_status", "note", "created_at"]
    can_delete = False

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "reporter", "area", "category", "status", "created_at"]
    list_filter = ["status", "area", "category", "created_at"]
    search_fields = ["title", "description", "location", "reporter__email"]
    readonly_fields = ["created_at", "updated_at", "resolved_at"]
    inlines = [StatusHistoryInline]

admin.site.register(Verification)
admin.site.register(Comment)
admin.site.register(Upvote)
admin.site.register(Notification)
