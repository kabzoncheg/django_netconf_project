from django.shortcuts import render
from django.shortcuts import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import DataError

from .forms import SearchForm
from .models import *
from .workertasks import rpc_update


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
    # This view implements search funtionality based on some different model fields
    # param: context_to_models - provides match functionality between values provided with URL
    #       and different models fields.
    if request.method == 'GET':
        form = SearchForm()
        if 'criteria' in request.GET :
            form = SearchForm(request.GET)
            if form.is_valid():
                criteria = form.cleaned_data['criteria']
                pattern = form.cleaned_data['pattern']
                return HttpResponseRedirect(reverse('devices:search',
                                                    kwargs={'match_context': criteria, 'match_value': pattern}))
        context_to_models = {'model': (Device, 'model'),
                            'instance-name': (DeviceInstance, 'instance_name'),
                            'mac-address': (InstanceArpTable, 'mac_address'),
                            'interface-ip-address': (InstanceLogInterface, 'ifa_local')}
        if match_context in context_to_models:
            model = context_to_models[match_context][0]
            model_field_name = context_to_models[match_context][1]
            try:
                context_obj_list = model.objects.filter(**{model_field_name: match_value})
                # Dirty Hack, cant call context_obj_list directly!!!
                print(context_obj_list)
            except DataError:
                error_text = 'Invalid search input'
                return render(request, 'devices/search.html', {'error': error_text})
            else:
                if context_obj_list and model != Device:
                    ip_addr_list = list(obj.related_device_id for obj in context_obj_list)
                    device_list = list(Device.objects.get(ip_address=ip_addr) for ip_addr in ip_addr_list)
                    return render(request, 'devices/search.html', {'device_list': device_list, 'form': form})
                elif context_obj_list and model == Device:
                    return render(request, 'devices/search.html', {'device_list': context_obj_list, 'form': form})
                else:
                    error_text = 'Nothing was found with specified parameters: ' \
                                 'criteria - {}, pattern - {}'.format(match_context, match_value)
                    return render(request, 'devices/search.html', {'error': error_text, 'form': form})


@login_required
def json_device_update(request):
    # This view accepts AJAX request and performs models update on demand via workertasks.py module.
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


@login_required
def device_detail(request, ip_address):
    device = get_object_or_404(Device, ip_address=ip_address)
    return render(request, 'devices/detail.html', {'device_obj': device})


@login_required
def device_instances(request, ip_address):
    device_instances = DeviceInstance.objects.filter(related_device_id=ip_address)
    try:
        return render(request, 'devices/instance.html', {'instances': device_instances, 'device_ip': ip_address})
    except:
        return Http404


@login_required
def device_rib(request, ip_address):
    device_instances = InstanceRIB.objects.filter(related_device_id=ip_address)
    try:
        return render(request, 'devices/rib.html', {'tables': device_instances, 'device_ip': ip_address})
    except:
        return Http404


@login_required
def device_arp(request, ip_address):
    device_instances = InstanceArpTable.objects.filter(related_device_id=ip_address)
    try:
        return render(request, 'devices/arp.html', {'tables': device_instances, 'device_ip': ip_address})
    except:
        return Http404


@login_required
def device_routes(request, ip_address):
    device_instances = InstanceRouteTable.objects.filter(related_device_id=ip_address).order_by('rt_destination_prefix')
    try:
        return render(request, 'devices/routes.html', {'tables': device_instances, 'device_ip': ip_address})
    except:
        return Http404


@login_required
def device_interfaces(request, ip_address):
    device_instances = InstancePhyInterface.objects.filter(related_device_id=ip_address)
    try:
        return render(request, 'devices/interfaces.html', {'interfaces': device_instances,
                                                                'device_ip': ip_address})
    except:
        return Http404


@login_required
def device_sub_interfaces(request, ip_address):
    device_instances = InstanceLogInterface.objects.filter(related_device_id=ip_address)
    try:
        return render(request, 'devices/subinterfaces.html', {'interfaces': device_instances,
                                                                'device_ip': ip_address})
    except:
        return Http404