# Path: articles/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Article, Reaction

# تسجيل موديل التفاعلات في لوحة التحكم
admin.site.register(Reaction)

# إجراءات مخصصة للأدمن داخل الداشبورد للموافقة أو الرفض دفعة واحدة
@admin.action(description="Approve selected articles")
def approve(modeladmin, request, queryset):
    queryset.update(status='Approved')

@admin.action(description="Reject selected articles")
def reject(modeladmin, request, queryset):
    queryset.update(status='Rejected')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['author', 'colored_status', 'title', 'specialization']
    list_filter = ['status', 'specialization']
    actions = [approve, reject]
    
    # دالة تلوين النصوص لتسهيل الفرز البصري للحالات داخل الجدول
    def colored_status(self, obj):
        colors = {
            'Approved': 'green',
            'Rejected': 'red',
            'Pending': 'orange'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )
    colored_status.short_description = 'Status'