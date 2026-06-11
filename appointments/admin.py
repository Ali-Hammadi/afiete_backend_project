from django.contrib import admin
from django.db import transaction
from decimal import Decimal
from .models import Appointment, Payment

@admin.action(description='Approve Selected Payments')
@transaction.atomic
def approve_payment(modeladmin, request, queryset):
    """
    Admin manually reviews the transaction and patient interfaces. Upon approval:
    1. Payment status changes to 'completed'.
    2. Platform commission (e.g., 20%) and doctor share (80%) are manually calculated and documented.
    3. The associated appointment status updates to 'confirmed'.
    """
    for payment in queryset:
        if payment.status == 'pending':
            payment.status = 'completed'
            
            # Manually calculate financial split upon approval (e.g., 20% admin commission)
            payment.admin_commission = payment.amount * Decimal('0.20')
            payment.doctor_amount = payment.amount - payment.admin_commission
            payment.save()
            
            # Programmatically update the associated appointment status to appear confirmed for both parties
            appointment = payment.appointment
            appointment.status = 'confirmed'
            appointment.payment_status = 'pending'  # Pending subsequent transfer to the doctor after the session
            appointment.save()

@admin.action(description='Mark as Transferred to Doctor')
@transaction.atomic
def mark_as_transferred_to_doctor(modeladmin, request, queryset):
    """
    After manually concluding the session and verifying the doctor's attendance, 
    the admin transfers the dues and updates the status to log the outflow of funds 
    from the app's bank account to the doctor.
    """
    for payment in queryset:
        # Ensure the patient's payment is completed first and the doctor hasn't received it yet
        if payment.status == 'completed' and not payment.is_transferred_to_doctor:
            payment.is_transferred_to_doctor = True
            payment.status = 'transferred'
            payment.save()
            
            appointment = payment.appointment
            appointment.payment_status = 'transferred'
            appointment.save()

@admin.action(description='Manual Refund to Patient')
@transaction.atomic
def refund_payment_to_patient(modeladmin, request, queryset):
    """
    In case of a doctor no-show (Missed) or if the patient cancels a refundable booking,
    the admin triggers this action to document the refund to the patient and clear the doctor's share.
    """
    for payment in queryset:
        if payment.status in ['pending', 'completed'] and not payment.is_transferred_to_doctor:
            payment.status = 'refunded'
            payment.admin_commission = Decimal('0.00')
            payment.doctor_amount = Decimal('0.00')
            payment.save()
            
            appointment = payment.appointment
            appointment.payment_status = 'refunded'
            appointment.status = 'cancelled'
            appointment.save()

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'amount', 'admin_commission', 'doctor_amount', 'status', 'is_transferred_to_doctor', 'created_at']
    list_filter = ['status', 'is_transferred_to_doctor']
    # Add strict manual management actions documented in the dashboard
    actions = [approve_payment, mark_as_transferred_to_doctor, refund_payment_to_patient]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'patient', 'status', 'payment_status', 'date')
    list_filter = ('status', 'payment_status')
    search_fields = ('doctor__user__username', 'patient__user__username')