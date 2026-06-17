from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Import only what we need for the mobile apps
from notes.urls import patient_router, doctor_router

urlpatterns = [
    # لوحة تحكم دجانغو المدمجة
    path('admin/', admin.site.urls),

    # 1. روابط المصادقة والحسابات والميزات المشتركة (تخدم المريض والطبيب معاً)
    path('api/auth/', include('users.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),    
    path('api/reports/', include('reports.urls')),

    # 2. بوابة المريض (Patient App Gateway)
    path('api/patient/', include([
        path('', include('patients.urls_patient')),                  
        path('doctors/', include('doctors.urls_patient')),           
        path('appointments/', include('appointments.urls_patient')), 
        path('articles/', include('articles.urls_patient')),         
        path('assessment/', include('assessments.urls')),            
        path('ratings/', include('ratings.urls')),
        # ❌ تم حذف الـ reports من هنا لأنه انتقل للأعلى كقسم مشترك
        path('notes/', include(patient_router.urls)), 
    ])),

    # 3. بوابة الطبيب (Doctor App Gateway)
    path('api/doctor/', include([
        path('', include('doctors.urls_doctor')),                    
        path('appointments/', include('appointments.urls_doctor')),  
        path('articles/', include('articles.urls_doctor')),          
        path('patients/', include('patients.urls_doctor')), 
        path('notes/', include(doctor_router.urls)), 
    ])),

    # توثيق السويغر
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)