from rest_framework import serializers
from .models import AppReport, UserReport

class AppReportSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='author.id', read_only=True)
    reportType = serializers.CharField(source='report_type', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    resolvedAt = serializers.DateTimeField(source='resolved_at', read_only=True)

    class Meta:
        model = AppReport
        fields = ['id', 'userId', 'reportType', 'reason', 'description', 'status', 'createdAt', 'resolvedAt']
        read_only_fields = ['id', 'userId', 'reportType', 'status', 'createdAt', 'resolvedAt']


class UserReportSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='author.id', read_only=True)
    reportType = serializers.CharField(source='report_type')
    targetId = serializers.CharField(source='target_id', required=False, allow_null=True)
    targetName = serializers.CharField(source='target_name', required=False, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    resolvedAt = serializers.DateTimeField(source='resolved_at', read_only=True)

    class Meta:
        model = UserReport
        fields = [
            'id', 'userId', 'reportType', 'targetId', 'targetName', 
            'reason', 'description', 'status', 'createdAt', 'resolvedAt', 'action_taken'
        ]
        read_only_fields = ['id', 'userId', 'status', 'createdAt', 'resolvedAt', 'action_taken']

    def validate_report_type(self, value):
        if value not in ['doctor', 'session']:
            raise serializers.ValidationError("User report type must be either 'doctor' or 'session'.")
        return value