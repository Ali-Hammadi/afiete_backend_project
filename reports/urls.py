from django.urls import path
from .views import CreateAppReportView, CreateUserReportView, MyReportsListView, ReportConfigView

urlpatterns = [
    path('config/', ReportConfigView.as_view(), name='report-config'),
    path('app/create/', CreateAppReportView.as_view(), name='app-report-create'),
    path('user/create/', CreateUserReportView.as_view(), name='user-report-create'),
    path('my-reports/', MyReportsListView.as_view(), name='my-reports-list'),
]