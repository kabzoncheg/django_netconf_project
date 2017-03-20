import logging
import os
import json
import zipfile
from io import BytesIO

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import DataError
from django.shortcuts import reverse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from django_netconf.common.workertasks import multiple_get_request
from django_netconf.config.settings import STATICFILES_DIRS

from devices.models import Device

from .models import Configurations
from .models import SetChain
from .models import SetRequest
from .forms import UploadConfigForm
from .forms import ChainCreateForm


logger = logging.getLogger(__name__)


@login_required
def single_set(request):
    return render(request, 'set/index.html')


@login_required
def configurations_list(request):
    error = None
    form = UploadConfigForm()
    configurations_list = Configurations.objects.filter(user=request.user).order_by('name')
    if request.method == 'POST':
        form = UploadConfigForm(request.POST, request.FILES)
        if form.is_valid():
            # config_name = form.cleaned_data['config_name']
            config_description = form.cleaned_data['config_description']
            user = request.user
            configs = request.FILES.getlist('config')
            duplicate_file_names = []
            for config in configs:
                instance = Configurations(name=config.name, description=config_description,
                                          mime_type=config.content_type, user=user, config=config)
                try:
                    instance.save()
                except IntegrityError:
                    duplicate_file_names.append(config.name)
            if duplicate_file_names:
                error = 'File(s) with folowing name(s) {} already exist(s)!'.format(duplicate_file_names)
    return render(request, 'set/configurations.html', {'form': form, 'configurations_list': configurations_list,
                                                       'error': error})


@login_required
def configurations_detail(request, config_id):
    instance = Configurations.objects.get(id=config_id, user_id=request.user.id)
    file = instance.config.read()
    return render(request, 'set/configurations_detail.html', {'config_file': file})


@login_required
def json_configurations_delete(request):
    if request.is_ajax() and request.method == 'GET':
        get = request.GET
        result = {}
        json_data = json.loads(get[u'config_id_list'])
        for element in json_data:
            try:
                instance = Configurations.objects.get(id=element)
                if request.user.id == instance.user_id:
                    instance.delete()
                    result[element] = True
                else:
                    result[element] = False
            except ObjectDoesNotExist:
                pass
            except Exception:
                result[element] = False
        return JsonResponse(result)


@login_required
def chain_list(request):
    try:
        chain_objects_list = SetChain.objects.filter(user=request.user).order_by('name')
    except DataError:
        chain_objects_list = []
    return render(request, 'set/chain_list.html', {'chain_list': chain_objects_list})


@login_required
def chain_create(request):
    form = ChainCreateForm()
    if request.method == 'POST':
        form = ChainCreateForm(request.POST)
        if form.is_valid():
            chain_name = form.cleaned_data['name']
            chain_description = form.cleaned_data['description']
            chain_user = request.user
            new_chain = SetChain(name=chain_name, description=chain_description, user=chain_user)
            new_chain.save()
            return HttpResponseRedirect(reverse('set:chain_list'))
    return render(request, 'set/chain_create.html', {'form': form})


@login_required
def chain_detail(request, name):
    chain = get_object_or_404(Chain, name=name, user=request.user)
    chain_requests = chain.requests.all()
    form = SingleGETRequestForm()
    if request.method == 'POST':
        form = SingleGETRequestForm(request.POST)
        if form.is_valid():
            ip_addr = form.cleaned_data['ip_address'].ip_address
            input_type = form.cleaned_data['input_type']
            input_value = form.cleaned_data['input_value']
            additional_input_value = form.cleaned_data['additional_input_value']
            device = Device.objects.get(ip_address=ip_addr)
            req = Request(device=device, input_type=input_type, input_value=input_value,
                          additional_input_value=additional_input_value)
            req.save()
            chain.requests.add(req)
            return HttpResponseRedirect(reverse('set:chain_detail', kwargs={'name': name}))
    return render(request, 'set/chain_detail.html', {'form': form, 'chain': chain, 'requests': chain_requests})