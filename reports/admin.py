from django.contrib import admin, messages
from .models import AppReport, UserReport

@admin.register(AppReport)
class AppReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'report_type', 'is_resolved', 'created_at')
    list_filter = ('report_type', 'is_resolved', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    actions = ['mark_as_resolved']

    @admin.action(description='Mark selected app reports as resolved')
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
        self.message_user(request, "Selected app reports have been successfully marked as resolved.", messages.SUCCESS)


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'reported_user', 'action_taken', 'created_at')
    list_filter = ('action_taken', 'created_at')
    search_fields = ('content', 'author__username', 'reported_user__username')
    readonly_fields = ('created_at',)
    
    actions = ['freeze_user_funds', 'suspend_user_account', 'delete_user_account', 'dismiss_report']

    @admin.action(description='Freeze reported user financial funds')
    def freeze_user_funds(self, request, queryset):
        success_count = 0
        for report in queryset:
            user = report.reported_user
            if user:
                if hasattr(user, 'is_funds_frozen'):
                    user.is_funds_frozen = True
                    user.save()
                
                report.action_taken = 'FUNDS_FROZEN'
                report.admin_notes = "Financial funds frozen by administrator due to user report."
                report.save()
                success_count += 1
                
        self.message_user(
            request, 
            f"Successfully froze funds for {success_count} user(s).", 
            messages.WARNING
        )

    @admin.action(description='Suspend reported user account (Temporary Ban)')
    def suspend_user_account(self, request, queryset):
        success_count = 0
        for report in queryset:
            user = report.reported_user
            if user:
                user.is_active = False  
                user.save()
                
                report.action_taken = 'ACCOUNT_SUSPENDED'
                report.admin_notes = "Account temporarily suspended by administrator."
                report.save()
                success_count += 1
                
        self.message_user(request, f"Successfully suspended accounts for {success_count} user(s).", messages.SUCCESS)

    @admin.action(description='Deactivate reported user account (Soft Delete)')
    def delete_user_account(self, request, queryset):
        """
        تحديث مطور: يقوم بتعطيل الحساب ومنع تسجيل الدخول (Soft Delete) 
        بدلاً من حذفه نهائياً لحماية سلامة المواعيد والسجلات المالية للتطبيق.
        """
        success_count = 0
        for report in queryset:
            user = report.reported_user
            if user:
                # الحفاظ على الكيان البرمجي مع سحب صلاحية النشاط
                user.is_active = False  
                user.save()
                
                report.action_taken = 'ACCOUNT_DELETED'
                report.admin_notes = "Account permanently deactivated (Soft Delete) by admin due to critical violations."
                report.save()
                success_count += 1
            
        self.message_user(
            request, 
            f"Successfully deactivated {success_count} account(s). No historical data was lost.", 
            messages.SUCCESS
        )

    @admin.action(description='Dismiss selected reports (No penalty)')
    def dismiss_report(self, request, queryset):
        queryset.update(action_taken='DISMISSED', admin_notes="Report investigated and dismissed by admin.")
        self.message_user(request, "Selected reports have been dismissed without any penalties.", messages.INFO)