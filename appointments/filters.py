from .models import Appointment
import django_filters

class AppointmentFilter(django_filters.FilterSet):
    date_from = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    date = django_filters.DateFilter(method='filter_by_date')  # ⬅️
    status = django_filters.ChoiceFilter(choices=Appointment.Status.choices)

    def filter_by_date(self, queryset, name, value):
        return queryset.filter(
            date__date=value  #  يفلتر على اليوم فقط بدون الوقت
        )

    class Meta:
        model = Appointment
        fields = ['status', 'date_from', 'date_to', 'date']


    # /api/appointments/my-appointments/?status=&date_from=&date_to=&date=2026-6-8