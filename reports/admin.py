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
    
    # Custom Admin Actions to handle penalties
    actions = ['freeze_user_funds', 'suspend_user_account', 'delete_user_account', 'dismiss_report']

    @admin.action(description='Freeze reported user financial funds')
    def freeze_user_funds(self, request, queryset):
        success_count = 0
        for report in queryset:
            user = report.reported_user
            if user:
                # Dynamically checks if 'is_funds_frozen' field exists in your Custom User model
                if hasattr(user, 'is_funds_frozen'):
                    user.is_funds_frozen = True
                    user.save()
                
                report.action_taken = 'FUNDS_FROZEN'
                report.save()
                success_count += 1
                
        self.message_user(
            request, 
            f"Successfully froze funds for {success_count} user(s). (Make sure 'is_funds_frozen' exists in your User model)", 
            messages.WARNING
        )

    @admin.action(description='Suspend reported user account (Temporary Ban)')
    def suspend_user_account(self, request, queryset):
        success_count = 0
        for report in queryset:
            user = report.reported_user
            if user:
                user.is_active = False  # Standard Django field to deactivate / block logins
                user.save()
                
                report.action_taken = 'ACCOUNT_SUSPENDED'
                report.save()
                success_count += 1
                
        self.message_user(request, f"Successfully deactivated/suspended accounts for {success_count} user(s).", messages.SUCCESS)

    @admin.action(description='Delete reported user account PERMANENTLY')
    def delete_user_account(self, request, queryset):
        success_count = 0
        for report in queryset:
            user = report.reported_user
            if user:
                user.delete()  # Removes the user record completely from the database
                
            report.action_taken = 'ACCOUNT_DELETED'
            report.save()
            success_count += 1
            
        self.message_user(request, f"Permanently deleted accounts for {success_count} user(s) from the database.", messages.ERROR)

    @admin.action(description='Dismiss selected reports (No penalty)')
    def dismiss_report(self, request, queryset):
        queryset.update(action_taken='DISMISSED')
        self.message_user(request, "Selected reports have been dismissed without any penalties.", messages.INFO)