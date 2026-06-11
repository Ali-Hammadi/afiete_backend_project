from rest_framework import serializers
from .models import AppReport, UserReport

class AppReportSerializer(serializers.ModelSerializer):
    # حقل إضافي لعرض النص المقروء لنوع البلاغ بدلاً من الرمز (مثل: Technical Bug بدلاً من BUG)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)

    class Meta:
        model = AppReport
        fields = ['id', 'report_type', 'report_type_display', 'title', 'content', 'created_at', 'is_resolved']
        read_only_fields = ['author', 'created_at', 'is_resolved', 'report_type_display']


class UserReportSerializer(serializers.ModelSerializer):
    # عرض اسم المستخدم المشتكى عليه لتسهيل قراءة الاستجابة في الفرونت إند
    reported_username = serializers.CharField(source='reported_user.username', read_only=True)

    class Meta:
        model = UserReport
        fields = ['id', 'reported_user', 'reported_username', 'content', 'created_at', 'action_taken']
        read_only_fields = ['author', 'created_at', 'action_taken', 'reported_username']