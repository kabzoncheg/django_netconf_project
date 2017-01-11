import json

from django.shortcuts import render
from django.http import Http404
from django.http import HttpResponseBadRequest
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required

from .models import Device
from .models import DeviceInstance
from .models import InstanceArpTable
from .models import InstanceLogInterface


@login_required
def device_list_view(request):
    device_objects = Device.objects.all().order_by('ip_address')
    return render(request, 'devices/index.html', {'device_list': device_objects})


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


def json_device_update(request):
    if request.is_ajax() and request.method == u'GET':
        get = request.GET
        result = {'success': False}
        if u'ip_address' in get:
            device_ip = get[u'ip_address']
            result['success'] = True
            result['device_ip'] = device_ip
        return JsonResponse(result)
    else:
        return HttpResponseBadRequest


