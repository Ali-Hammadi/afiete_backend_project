from django.contrib import admin
from .models import *
def approve_payment(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status == 'pending':
            payment.status = 'completed'
            payment.viewed_by = request.user
            payment.save()
            payment.appointment.status = 'confirmed'
            payment.appointment.save()

approve_payment.short_description = "Approve selected payments"


def reject_payment(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status == 'pending':
            payment.status = 'rejected'
            payment.viewed_by = request.user
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

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'amount', 'method', 'status', 'date']
    list_filter = ['status', 'method']
    actions = [approve_payment, reject_payment, refund_payment]

    
Models = [
    Appointment,
    Prescription,   
    Medication,
    SessionPrice,
]

admin.site.register(Models)