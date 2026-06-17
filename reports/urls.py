from django.urls import path
from .views import (
    ReportConfigView, 
    CreateAppReportView, 
    CreateUserReportView, 
    MyReportsListView
)

urlpatterns = [
    # 1. جلب الإعدادات والأسباب ديناميكياً (مشترك للمريض والطبيب)
    path('config/', ReportConfigView.as_view(), name='report-config'),
    
    # 2. إنشاء بلاغ خاص بالتطبيق (مشكلة تقنية أو اقتراح)
    path('app/create/', CreateAppReportView.as_view(), name='app-report-create'),
    
    # 3. إنشاء بلاغ ضد مستخدم آخر (طبيب أو مريض)
    path('user/create/', CreateUserReportView.as_view(), name='user-report-create'),
    
    # 4. عرض السجل الخاص بالمستخدم الحالي فقط (مريض أو طبيب) بناءً على الـ Token
    path('my-reports/', MyReportsListView.as_view(), name='my-reports-list'),
]