from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, Http404
from django.views import generic
from django.core.urlresolvers import reverse
from django.utils import timezone

from .models import Device

class DeviceListView(generic.ListView):
    model = Device
    template_name = 'devices/index.html'
    context_object_name = 'device_list'
    paginate_by = 10

    def get_queryset(self):
        return Device.objects.order_by('ip_address')
