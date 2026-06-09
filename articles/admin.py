# Path: articles/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Article, Reaction

# تسجيل موديل التفاعلات في لوحة التحكم بشكل بسيط
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
    # 1. تحسين العرض ليشمل التاريخ والوقت والحالة الملونة
    list_display = ['title', 'author', 'specialization', 'colored_status', 'created_at']
    
    # 2. إضافة فلاتر ذكية وسريعة للأدمن في القائمة الجانبية
    list_filter = ['status', 'specialization', 'created_at']
    
    # 3. تفعيل ميزة البحث بالـ Title أو اسم الطبيب أو تخصص الطبيب لسهولة الوصول
    search_fields = ['title', 'content', 'author__user__username']
    
    # الإجراءات الجماعية (الموافقة والرفض)
    actions = [approve, reject]
    
    # 4. تحسين أداء الاستعلامات (مهم جداً لمنع بطء لوحة التحكم أونلاين)
    list_select_related = ['author', 'author__user', 'specialization']

    # دالة تلوين النصوص لتسهيل الفرز البصري للحالات داخل الجدول
    def colored_status(self, obj):
        colors = {
            'Approved': '#2ecc71',  # أخضر مريح للعين
            'Rejected': '#e74c3c',  # أحمر واضح
            'Pending': '#e67e22'   # برتقالي للتنبيه
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )
    
    colored_status.short_description = 'Status'