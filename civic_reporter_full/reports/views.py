from django.utils import timezone
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from .models import Area, Category, Report, StatusHistory, Comment, Upvote, Verification, Notification
from .permissions import IsAdminOrStaff, ReportAccessPermission
from .serializers import AreaSerializer, CategorySerializer, ReportSerializer, CommentSerializer, CommentCreateSerializer, StatusUpdateSerializer

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    def get_permissions(self):
        return [permissions.IsAuthenticated()] if self.action in ("list", "retrieve") else [IsAdminOrStaff()]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        return [permissions.IsAuthenticated()] if self.action in ("list", "retrieve") else [IsAdminOrStaff()]

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated, ReportAccessPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        qs = Report.objects.select_related("reporter", "area", "category").prefetch_related("comments__author", "status_history__changed_by", "verifications__verifier").annotate(upvote_count=Count('upvotes'))
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return qs
        if user.is_authority:
            try:
                area_id = user.authorityprofile.area_id
                return qs.filter(area_id=area_id) if area_id else qs
            except Exception:
                return qs.none()
        return qs

    def perform_create(self, serializer):
        report = serializer.save(reporter=self.request.user)
        StatusHistory.objects.create(report=report, changed_by=self.request.user, old_status="", new_status=report.status, note="Report submitted")
        Notification.objects.create(user=self.request.user, report=report, message=f"Your report '{report.title}' was submitted.")

    def update(self, request, *args, **kwargs):
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser or request.user.is_authority):
            return Response({"detail": "Only an authority can edit a report after submission."}, status=403)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def comments(self, request, pk=None):
        report = self.get_object()
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(report=report, author=request.user, **serializer.validated_data)
        if report.reporter_id != request.user.id:
            Notification.objects.create(user=report.reporter, report=report, message=f"{request.user.name} commented on '{report.title}'.")
        return Response(CommentSerializer(comment).data, status=201)

    @action(detail=True, methods=["post"])
    def upvote(self, request, pk=None):
        report = self.get_object()
        if report.reporter_id == request.user.id:
            return Response({"detail": "You cannot upvote your own report."}, status=400)
        _, created = Upvote.objects.get_or_create(report=report, user=request.user)
        if not created:
            Upvote.objects.filter(report=report, user=request.user).delete()
        return Response({"upvoted": created, "upvote_count": report.upvotes.count()})

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        report = self.get_object()
        if report.reporter_id == request.user.id:
            return Response({"detail": "You cannot verify your own report."}, status=400)
        is_authority = request.user.is_staff or request.user.is_superuser or request.user.is_authority
        if not is_authority:
            return Response({"detail": "Only an authority can submit an official verification."}, status=403)
        value = request.data.get("is_valid")
        if not isinstance(value, bool):
            return Response({"is_valid": ["Send true or false."]}, status=400)
        verification, _ = Verification.objects.update_or_create(report=report, verifier=request.user, defaults={"is_valid": value, "note": str(request.data.get("note", ""))[:500]})
        if value and report.status in (Report.Status.SUBMITTED, Report.Status.UNDER_REVIEW):
            self._set_status(report, Report.Status.VERIFIED, request.user, "Official verification")
        return Response({"id": verification.id, "is_valid": verification.is_valid, "note": verification.note})

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser or request.user.is_authority):
            return Response({"detail": "Only an authority can change report status."}, status=403)
        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        note = serializer.validated_data.get("note", "")
        if new_status == Report.Status.RESOLVED and not report.resolution_photo:
            uploaded = request.FILES.get("resolution_photo")
            if uploaded:
                report.resolution_photo = uploaded
            else:
                return Response({"detail": "Upload a resolution photo before marking the issue resolved."}, status=400)
        self._set_status(report, new_status, request.user, note)
        if "resolution_photo" in request.FILES:
            report.resolution_photo = request.FILES["resolution_photo"]
            report.save(update_fields=["resolution_photo"])
        return Response(ReportSerializer(report, context={"request": request}).data)

    def _set_status(self, report, new_status, user, note=""):
        old_status = report.status
        report.status = new_status
        report.resolved_at = timezone.now() if new_status == Report.Status.RESOLVED else None
        report.save(update_fields=["status", "resolved_at", "updated_at", "resolution_photo"])
        StatusHistory.objects.create(report=report, changed_by=user, old_status=old_status, new_status=new_status, note=note)
        recipients = set(report.area.residents.exclude(id=report.reporter_id).values_list("id", flat=True))
        recipients.add(report.reporter_id)
        Notification.objects.bulk_create([Notification(user_id=uid, report=report, message=f"Report '{report.title}' status changed to {report.get_status_display()}.") for uid in recipients])

    @action(detail=False, methods=["get"])
    def mine(self, request):
        qs = Report.objects.filter(reporter=request.user).select_related("area", "category").annotate(upvote_count=Count('upvotes'))
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def notifications(self, request):
        items = Notification.objects.filter(user=request.user).values("id", "report_id", "message", "is_read", "created_at")[:50]
        return Response(list(items))
