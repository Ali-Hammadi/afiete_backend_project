from django.contrib import admin
from .models import Patient
# Register your models here.
Modules = [
    Patient,]

admin.site.register(Modules)