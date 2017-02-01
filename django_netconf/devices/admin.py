from django.contrib import admin

from .models import Device


class DeviceAdmin(admin.ModelAdmin):
    fields = ['ip_address', 'description']

admin.site.register(Device, DeviceAdmin)
