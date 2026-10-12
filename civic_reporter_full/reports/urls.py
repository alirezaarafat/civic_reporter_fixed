from rest_framework.routers import DefaultRouter
from .views import AreaViewSet, CategoryViewSet, ReportViewSet

router = DefaultRouter()
router.register("areas", AreaViewSet, basename="area")
router.register("categories", CategoryViewSet, basename="category")
router.register("", ReportViewSet, basename="report")
urlpatterns = router.urls
