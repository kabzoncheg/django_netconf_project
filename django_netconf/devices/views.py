from django.shortcuts import render
from django.shortcuts import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from .forms import SearchForm
from .models import Device
from .models import DeviceInstance
from .models import InstanceArpTable
from .models import InstanceLogInterface
from .workertasks import rpc_update


context_to_models = {'model': (Device, 'model'),
                    'instance-name': (DeviceInstance, 'instance_name'),
                    'mac-address': (InstanceArpTable, 'mac_address'),
                    'interface-ip-address': (InstanceLogInterface, 'ifa_local')}
context_to_models_list = list(context_to_models.keys())


@login_required
def device_list_view(request):
    if request.method == 'GET':
        form = SearchForm()
        device_objects = Device.objects.all().order_by('ip_address')
        if 'criteria' in request.GET :
            form = SearchForm(request.GET)
        if form.is_valid():
            criteria = form.cleaned_data['criteria']
            pattern = form.cleaned_data['pattern']
            return HttpResponseRedirect(reverse('devices:search',
                                                kwargs={'match_context': criteria, 'match_value': pattern}))
        return render(request, 'devices/index.html', {'device_list': device_objects, 'form': form})


@login_required
def device_list_search_universal(request, match_context, match_value):
    global context_to_models
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


@login_required
def json_device_update(request):
    # this view accepts AJAX request and performs Device model update on demand via workertasks.py module
    if request.is_ajax() and request.method == 'GET':
        get = request.GET
        result = {'status': False}
        if u'ip_address' in get:
            device_ip = get[u'ip_address']
            try:
                Device.objects.get(ip_address=device_ip)
            except ObjectDoesNotExist:
                pass
            else:
                rpc_status = rpc_update(device_ip)
                if rpc_status == 1:
                    dev_obj = Device.objects.get(ip_address=device_ip)
                    result = dev_obj.__dict__
                    result['status'] = True
                    result['device_ip'] = device_ip
                    import re
                    keys_to_remove = list(key for key in result if re.match('^_.+', key))
                    if keys_to_remove:
                        for item in keys_to_remove:
                            result.__delitem__(item)
        return JsonResponse(result)
