from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorityOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser or user.is_authority))


class ReportAccessPermission(BasePermission):
    """Citizens can create/read their own reports; authorities can manage reports in their area."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        if getattr(view, "action", None) in ("comments", "upvote"):
            return True
        if obj.reporter_id == user.id and request.method in ("DELETE",):
            return obj.status == "submitted"
        if not user.is_authority:
            return False
        try:
            return user.authorityprofile.area_id in (None, obj.area_id)
        except Exception:
            return False


class IsAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
