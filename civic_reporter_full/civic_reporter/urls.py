from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),

    # App1_accounts -> registration, login, token refresh, current-user
    path("api/auth/", include("accounts.urls")),

    # Issue reports, areas, categories, comments, votes, and status history
    path("api/reports/", include("reports.urls")),

    # Frontend (HTML/CSS/JS in /frontend), served by Django itself.
    # Home page:
    path("", serve, {"path": "index.html", "document_root": settings.FRONTEND_DIR}),
    # Every other frontend file (login.html, css/style.css, js/api.js, ...):
    re_path(
        r"^(?P<path>.+\.(?:html|css|js|svg|png|jpg|ico))$",
        serve,
        {"document_root": settings.FRONTEND_DIR},
    ),
]

# Report photos are public evidence attached to public civic reports. For production,
# prefer durable object storage/CDN rather than serving uploads through Django.
urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
