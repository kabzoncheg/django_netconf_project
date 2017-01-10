import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, Http404
from django.views import generic
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Device
from .models import DeviceInstance
from .models import InstanceArpTable
from .models import InstanceLogInterface


class DeviceListView(generic.ListView):
    model = Device
    template_name = 'devices/index.html'
    context_object_name = 'device_list'

    def get_queryset(self):
        return Device.objects.order_by('ip_address')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DeviceListView, self).dispatch(*args, **kwargs)


@login_required
def device_list_search_universal(request, match_context, match_value):
    context_to_models = {'model': (Device, 'model'),
                         'instance-name': (DeviceInstance, 'instance_name'),
                         'mac-address': (InstanceArpTable, 'mac_address'),
                         'interface-ip-address': (InstanceLogInterface, 'ifa_local')}
    if match_context in context_to_models:
        model = context_to_models[match_context][0]
        model_field_name = context_to_models[match_context][1]
        context_obj_list = model.objects.filter(**{model_field_name: match_value})
        if context_obj_list and model != Device:
            ip_addr_list = list(obj.related_device_id for obj in context_obj_list)
            device_list = list(Device.objects.get(ip_address=ip_addr) for ip_addr in ip_addr_list)
            return render(request, 'devices/index.html', {'device_list': device_list})
        elif context_obj_list and model == Device:
            return render(request, 'devices/index.html', {'device_list': context_obj_list})
    raise Http404
