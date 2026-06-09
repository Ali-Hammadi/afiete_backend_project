from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.contrib import admin
from django.urls import path , include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from doctors.views import ScheduleViewSet
from appointments.views import SessionPricesViewSet

router = DefaultRouter()
router.register(r'doctors/schedule', ScheduleViewSet, basename='schedule')
router.register(r'appointmetns/dcotors/prices', SessionPricesViewSet , basename='prices')

urlpatterns = [ 
    path('admin/', admin.site.urls),
    path('api/patients/', include('patients.urls')),
    path('api/users/', include('users.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/ratings/', include('ratings.urls')),
    path('api/relax/', include('musics.urls')),
    path('api/articles/', include('articles.urls')),

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # routers 
    path('api/' , include(router.urls))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
  