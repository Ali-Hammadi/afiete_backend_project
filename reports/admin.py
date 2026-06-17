from django.contrib import admin, messages
from django.utils import timezone
from .models import AppReport, UserReport

@admin.register(AppReport)
class AppReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'reason', 'status', 'created_at', 'resolved_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('description', 'author__username')
    actions = ['mark_as_resolved']

    @admin.action(description='Mark selected app reports as resolved')
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, "Selected app reports have been resolved.", messages.SUCCESS)


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'report_type', 'target_name', 'status', 'action_taken', 'created_at')
    list_filter = ('report_type', 'status', 'action_taken', 'created_at')
    search_fields = ('description', 'author__username', 'target_name', 'target_id')
    readonly_fields = ('created_at', 'resolved_at')
    
    actions = ['freeze_user_funds', 'suspend_user_account', 'delete_user_account', 'dismiss_report']

    def close_report(self, report, action_type, admin_notes):
        report.status = 'resolved'
        report.action_taken = action_type
        report.admin_notes = admin_notes
        report.resolved_at = timezone.now()
        report.save()

    @admin.action(description='Freeze reported user financial funds')
    def freeze_user_funds(self, request, queryset):
        success_count = 0
        for report in queryset:
            # هنا يمكنك جلب الـ User الفعلي بناءً على الـ target_id إذا كان النوع doctor
            if report.report_type == 'doctor' and report.target_id:
                from users.models import User
                try:
                    user = User.objects.get(pk=report.target_id)
                    if hasattr(user, 'is_funds_frozen'):
                        user.is_funds_frozen = True
                        user.save()
                except User.DoesNotExist:
                    pass
            
            self.close_report(report, 'FUNDS_FROZEN', "Financial funds frozen by administrator due to user report.")
            success_count += 1
                
        self.message_user(request, f"Successfully processed {success_count} report(s) and applied restrictions.", messages.WARNING)

    @admin.action(description='Suspend reported user account (Temporary Ban)')
    def suspend_user_account(self, request, queryset):
        success_count = 0
        for report in queryset:
            if report.report_type == 'doctor' and report.target_id:
                from users.models import User
                try:
                    user = User.objects.get(pk=report.target_id)
                    user.is_active = False
                    user.save()
                except User.DoesNotExist:
                    pass
            
            self.close_report(report, 'ACCOUNT_SUSPENDED', "Account temporarily suspended by administrator.")
            success_count += 1
                
        self.message_user(request, f"Successfully suspended accounts associated with {success_count} report(s).", messages.SUCCESS)

    @admin.action(description='Deactivate reported user account (Soft Delete)')
    def delete_user_account(self, request, queryset):
        success_count = 0
        for report in queryset:
            if report.report_type == 'doctor' and report.target_id:
                from users.models import User
                try:
                    user = User.objects.get(pk=report.target_id)
                    user.is_active = False
                    user.save()
                except User.DoesNotExist:
                    pass
            
            self.close_report(report, 'ACCOUNT_DELETED', "Account permanently deactivated (Soft Delete) by admin due to critical violations.")
            success_count += 1
            
        self.message_user(request, f"Successfully soft-deleted users for {success_count} report(s).", messages.SUCCESS)

    @admin.action(description='Dismiss selected reports (No penalty)')
    def dismiss_report(self, request, queryset):
        queryset.update(status='resolved', action_taken='DISMISSED', admin_notes="Report investigated and dismissed by admin.", resolved_at=timezone.now())
        self.message_user(request, "Selected reports have been dismissed without any penalties.", messages.INFO)