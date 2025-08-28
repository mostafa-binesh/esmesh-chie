from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
import django.conf.urls.static
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

schema_view = get_schema_view(
    openapi.Info(
        title="NaftKhabar API",
        default_version='v0.1',
        description="API documentation for Naft-Khabar API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="ubirockteam@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[SessionAuthentication, TokenAuthentication],
)

urlpatterns = [
                  path('admin/', admin.site.urls),
                  # authentication
                  path('api/auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
                  # people API
                  path('api/people/', include('people.urls')),
                  # Swagger paths
                  path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
                  path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
                  path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
                  re_path(r'^$', TemplateView.as_view(template_name='static_pages/index.html'), name='home'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
