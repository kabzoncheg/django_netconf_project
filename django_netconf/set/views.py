import logging
import os

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db import DataError
from django.shortcuts import reverse
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from django_netconf.common.workertasks import send_worker_request_and_zip_result
from django_netconf.common.views import JsonDeleteByIDView
from django_netconf.config.settings import STATICFILES_DIRS

from devices.models import Device

from .models import Configurations
from .models import SetChain
from .models import SetRequest
from .forms import UploadConfigForm
from .forms import ChainCreateForm
from .forms import SingleSETRequestForm


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


class JsonConfigurationsDelete(JsonDeleteByIDView):
    model = Configurations
    json_array_name = 'config_id_list'
    user_id_check = True


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
    chain = get_object_or_404(SetChain, name=name, user=request.user)
    chain_requests = chain.requests.all()
    form = SingleSETRequestForm()
    form.fields['config'].queryset = Configurations.objects.filter(user_id=request.user.id)
    if request.method == 'POST':
        form = SingleSETRequestForm(request.POST)
        if form.is_valid():
            ip_addr = form.cleaned_data['ip_address'].ip_address
            config_id = form.cleaned_data['config'].id
            device = Device.objects.get(ip_address=ip_addr)
            config = Configurations.objects.get(id=config_id)
            req = SetRequest(device=device, config=config)
            req.save()
            chain.requests.add(req)
            return HttpResponseRedirect(reverse('set:chain_detail', kwargs={'name': name}))
    return render(request, 'set/chain_detail.html', {'form': form, 'chain': chain, 'requests': chain_requests})


class JsonSetChainDelete(JsonDeleteByIDView):
    model = SetChain
    user_id_check = True


class JsonSetRequestDelete(JsonDeleteByIDView):
    model = SetRequest
    json_array_name = 'request_id_list'


@login_required
def multiple_set(request, chain_name, compare_flag):
    chain = get_object_or_404(SetChain, name=chain_name, user=request.user)
    chain_requests = chain.requests.all()
    worker_request_list = []
    path = os.path.join(STATICFILES_DIRS[0], 'temp')
    for ch_req in chain_requests:
        worker_request = {'host': ch_req.device_id, 'config_id': ch_req.config_id,
                          'file_path': path, 'compare_flag': compare_flag}
        worker_request_list.append(worker_request)
    in_memory_zip = send_worker_request_and_zip_result(worker_request_list, worker_name='SET')
    if in_memory_zip is None:
        return HttpResponse(status_code=200)
    in_memory_zip.seek(0)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=get_response.zip'
    response.write(in_memory_zip.read())
    return response
