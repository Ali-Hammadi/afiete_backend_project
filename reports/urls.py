from django.urls import path
from .views import CreateAppReportView, CreateUserReportView, MyReportsListView

urlpatterns = [
    # 1. إرسال بلاغ عن التطبيق (مشكلة تقنية أو اقتراح)
    path('app/create/', CreateAppReportView.as_view(), name='create-app-report'),
    
    # 2. إرسال بلاغ عن مستخدم آخر (طبيب أو مريض)
    path('user/create/<int:reported_user_id>/', CreateUserReportView.as_view(), name='create-user-report'),
    
    # 3. عرض قائمة البلاغات الخاصة بالمستخدم (سجل التقارير)
    path('my-reports/', MyReportsListView.as_view(), name='my-reports-list'),
]