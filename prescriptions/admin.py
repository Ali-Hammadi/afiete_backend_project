from django.contrib import admin

from .models import Prescription, PrescriptionMedication


class PrescriptionMedicationInline(admin.TabularInline):
    model = PrescriptionMedication
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        'prescription_number',
        'doctor',
        'patient',
        'appointment',
        'created_at',
    ]
    list_filter = ['created_at', 'doctor', 'patient']
    search_fields = [
        'prescription_number',
        'doctor__user__username',
        'doctor__user__email',
        'patient__user__username',
        'patient__user__email',
        'diagnosis',
    ]
    readonly_fields = ['prescription_number', 'created_at', 'updated_at']
    inlines = [PrescriptionMedicationInline]


@admin.register(PrescriptionMedication)
class PrescriptionMedicationAdmin(admin.ModelAdmin):
    list_display = ['medication_name', 'prescription', 'dosage', 'frequency', 'duration']
    search_fields = ['medication_name', 'prescription__prescription_number']
