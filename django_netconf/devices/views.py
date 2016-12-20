import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, Http404
from django.views import generic
from django.core.urlresolvers import reverse
from django.utils import timezone

from .models import Device
from .models import DeviceInstance


class DeviceListView(generic.ListView):
    model = Device
    template_name = 'devices/index.html'
    context_object_name = 'device_list'

    def get_queryset(self):
        return Device.objects.order_by('ip_address')


def device_list_search_vrf_view(request, vrf_name):
    vrf_list = DeviceInstance.objects.filter(instance_name=vrf_name)
    if vrf_list:
        ip_addr_list = list(vrf.related_device_id for vrf in vrf_list)
        device_list = list(Device.objects.get(ip_address=ip_addr) for ip_addr in ip_addr_list)
        return render(request, 'devices/index.html', {'device_list': device_list})
    else:
        raise Http404
