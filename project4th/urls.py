from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. روابط المصادقة والحسابات المشتركة
    path('api/auth/', include('users.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # 2. بوابة تطبيق المريض بالكامل (Patient App Gateway)
    path('api/patient/', include([
        path('', include('patients.urls')),  # حساب المريض نفسه
        path('doctors/', include('doctors.urls')), # رؤية الأطباء والتخصصات من منظور المريض
        path('appointments/', include('appointments.urls')), # حجوزات المريض ومدفوعاته
        path('articles/', include('articles.urls')), # تصفح المقالات والتفاعل معها
        # path('assessment/', include('assessment.urls')), # التقييم والنفسية (تأكد من إضافتها هنا)
    ])),

    # 3. بوابة تطبيق الطبيب بالكامل (Doctor App Gateway)
    path('api/doctor/', include([
        path('', include('doctors.urls')), # بروفايل الطبيب، أوقات الدوام، والتعليم
        path('appointments/', include('appointments.urls')), # لوحة تحكم الطبيب للمواعيد
        path('articles/', include('articles.urls')), # إدارة مقالات الطبيب (إنشاء، تعديل، حذف)
    ])),

    # السويغر والتوثيق
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)