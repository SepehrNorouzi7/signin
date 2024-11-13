from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Login API",
        default_version="v1",
        description="Login API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="sepehrnorouzi07@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("account/", include("django.contrib.auth.urls")),
    path("account/api/v1/", include("account.api.v1.urls")),
    path(
        "swagger/output.json",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
