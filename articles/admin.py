from django.contrib import admin
from django.utils.html import format_html
from .models import Article , Reaction

Models = [Reaction]
admin.site.register(Models) 

# actions in dashboard
@admin.action(description="Approve article")
def approve(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'Approved'
        obj.save()

@admin.action(description="Reject article")
def reject(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = 'Rejected'
        obj.save()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['author','colored_status','title', 'specialization']
    list_filter = ['status']
    actions = [approve,reject]
    def colored_status(self,obj):
        colors = {
            'Approved': 'green',
            'Rejected': 'red',
            'Pending': 'orange'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )