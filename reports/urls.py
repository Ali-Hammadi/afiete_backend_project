from django.urls import path
from .views import CreateAppReportView, CreateUserReportView, MyReportsListView

urlpatterns = [
    path('app/create/', CreateAppReportView.as_view(), name='app-report-create'),
    path('user/create/<int:reported_user_id>/', CreateUserReportView.as_view(), name='user-report-create'),
    path('my-reports/', MyReportsListView.as_view(), name='my-reports-list'),
]