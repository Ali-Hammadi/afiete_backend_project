from django.contrib import admin
from .models import *

def approve_payment(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status == 'pending':
            payment.status = 'completed'
            payment.viewed_by.add(request.user)  # تم الإصلاح هنا
            payment.save()
            payment.appointment.status = 'confirmed'
            payment.appointment.save()

approve_payment.short_description = "Approve selected payments"


def reject_payment(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status == 'pending':
            payment.status = 'rejected'
            payment.viewed_by.add(request.user)  # تم الإصلاح هنا
            payment.save()
            payment.appointment.status = 'cancelled'
            payment.appointment.save()

reject_payment.short_description = "Reject selected payments"


def refund_payment(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status == 'completed':
            payment.status = 'refunded'
            payment.appointment.status = 'cancelled'
            payment.appointment.save()
            payment.save()
            payment.viewed_by.add(request.user)
            print(f"viewed_by count: {payment.viewed_by.count()}")
            print(f"user: {request.user}")

refund_payment.short_description = "Refund selected payments"

# دالة إضافية للإدارة لتأكيد إرسال مستحقات الطبيب إليه
def mark_as_transferred_to_doctor(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status == 'completed' and not payment.is_transferred_to_doctor:
            payment.is_transferred_to_doctor = True
            payment.save()

mark_as_transferred_to_doctor.short_description = "Mark as transferred to Doctor"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'amount', 'admin_commission', 'doctor_amount', 'status', 'is_transferred_to_doctor', 'date']
    list_filter = ['status', 'is_transferred_to_doctor', 'method']
    actions = [approve_payment, reject_payment, refund_payment, mark_as_transferred_to_doctor]

    
Models = [
    Appointment,
    Prescription,   
    Medication,
    SessionPrice,
]

admin.site.register(Models)