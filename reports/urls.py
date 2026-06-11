from django.urls import path
from .views import CreateAppReportView, CreateUserReportView, MyReportsListView

urlpatterns = [
    # 1. إرسال بلاغ عن التطبيق (مشكلة تقنية أو اقتراح)
    path('app/create/', CreateAppReportView.as_view(), name='create-app-report'),
    
    # 2. إرسال بلاغ عن مستخدم آخر (يتم تمرير ID المستخدم في الرابط)
    path('user/create/<int:reported_user_id>/', CreateUserReportView.as_view(), name='create-user-report'),
    
    # 3. رابط رؤية الريبورتات السابقة (سجل التقارير المشترك)
    path('my-reports/', MyReportsListView.as_view(), name='my-reports-list'),
]