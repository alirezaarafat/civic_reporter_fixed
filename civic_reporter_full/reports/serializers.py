from rest_framework import serializers
from .models import Area, Category, Report, StatusHistory, Comment, Verification, Notification

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name", "location"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type"]

class StatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.name", read_only=True, default="System")
    class Meta:
        model = StatusHistory
        fields = ["id", "old_status", "new_status", "note", "changed_by_name", "created_at"]

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "author", "author_name", "body", "created_at"]
        read_only_fields = ["author"]

class VerificationSerializer(serializers.ModelSerializer):
    verifier_name = serializers.CharField(source="verifier.name", read_only=True)
    class Meta:
        model = Verification
        fields = ["id", "verifier_name", "is_valid", "note", "created_at"]

class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.name", read_only=True)
    area_name = serializers.CharField(source="area.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    upvote_count = serializers.IntegerField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)
    verifications = VerificationSerializer(many=True, read_only=True)
    class Meta:
        model = Report
        fields = ["id", "reporter", "reporter_name", "title", "description", "area", "area_name", "category", "category_name", "location", "latitude", "longitude", "photo", "resolution_photo", "status", "upvote_count", "comments", "status_history", "verifications", "created_at", "updated_at", "resolved_at"]
        read_only_fields = ["reporter", "status", "resolution_photo", "created_at", "updated_at", "resolved_at"]

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["body"]

class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Report.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
