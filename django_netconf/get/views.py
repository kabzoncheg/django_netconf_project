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

from django_netconf.common.workertasks import multiple_get_request
from django_netconf.config.settings import STATICFILES_DIRS

from devices.models import Device

from .forms import SingleGETRequestForm
from .forms import ChainCreateForm
from .models import Chain
from .models import Request


logger = logging.getLogger(__name__)


def send_worker_request_and_zip_result(task_list, path=os.path.join(STATICFILES_DIRS[0], 'temp')):
    file_names = multiple_get_request(task_list)
    if not file_names:
        return None
    in_memory = BytesIO()
    zip_archive = zipfile.ZipFile(in_memory, mode='w')
    for file_name in file_names:
        file_path = os.path.join(path, file_name)
        try:
            with open(file_path) as f:
                file_content = f.read()
            logger.info('Writing file at {} to in memory archive:'.format(file_path))
            zip_archive.writestr(file_name, file_content)
        except RuntimeError:
            logger.info('Got ERROR while writing file at {} to in memory archive:'.format(file_path))
            zip_archive.close()
        finally:
            logger.info('removing file {}:'.format(file_path))
            os.remove(file_path)
    zip_archive.close()
    return in_memory


@login_required
def single_get(request):
    form = SingleGETRequestForm()
    if request.method == 'POST':
        form = SingleGETRequestForm(request.POST)
        if form.is_valid():
            ip_addr = form.cleaned_data['ip_address'].ip_address
            input_type = form.cleaned_data['input_type']
            input_value = form.cleaned_data['input_value']
            additional_input_value = form.cleaned_data['additional_input_value']
            path = os.path.join(STATICFILES_DIRS[0], 'temp')
            request = {'host': ip_addr, 'input_type': input_type, 'input_value': input_value,
                       'additional_input_value': additional_input_value, 'file_path': path}
            in_memory_zip = send_worker_request_and_zip_result([request])
            if in_memory_zip is None:
                return HttpResponse(status_code=200)
            in_memory_zip.seek(0)
            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=get_response.zip'
            response.write(in_memory_zip.read())
            return response
    else:
        return render(request, 'get/index.html', {'form': form})


@login_required
def chain_list(request):
    try:
        chain_objects_list = Chain.objects.filter(user=request.user).order_by('name')
    except DataError:
        chain_objects_list = []
    return render(request, 'get/chain_list.html', {'chain_list': chain_objects_list})


@login_required
def chain_create(request):
    form = ChainCreateForm()
    if request.method == 'POST':
        form = ChainCreateForm(request.POST)
        if form.is_valid():
            chain_name = form.cleaned_data['name']
            chain_description = form.cleaned_data['description']
            chain_user = request.user
            new_chain = Chain(name=chain_name, description=chain_description, user=chain_user)
            new_chain.save()
            return HttpResponseRedirect(reverse('get:chain_list'))
    return render(request, 'get/chain_create.html', {'form': form})


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
            return HttpResponseRedirect(reverse('get:chain_detail', kwargs={'name': name}))
    return render(request, 'get/chain_detail.html', {'form': form, 'chain': chain, 'requests': chain_requests})


@login_required
def json_chain_delete(request):
    # This view accepts AJAX request and performs Chain model entries delete
    if request.is_ajax() and request.method == 'GET':
        get = request.GET
        result = {}
        chain_ids = json.loads(get[u'chain_id_list'])
        for chain_id in chain_ids:
            try:
                chain_obj = Chain.objects.get(id=chain_id)
                chain_obj.delete()
                result[chain_id] = True
            except ObjectDoesNotExist:
                pass
            except Exception:
                result[chain_id] = False
        return JsonResponse(result)


@login_required
def json_chain_request_delete(request):
    # This view accepts AJAX request and performs Request model entries delete
    if request.is_ajax() and request.method == 'GET':
        get = request.GET
        result = {}
        request_ids = json.loads(get[u'request_id_list'])
        for req_id in request_ids:
            try:
                req_obj = Request.objects.get(id=req_id)
                req_obj.delete()
                result[req_id] = True
            except ObjectDoesNotExist:
                pass
            except Exception:
                result[req_id] = False
        return JsonResponse(result)


@login_required
def multiple_get(request, chain_name):
    chain = get_object_or_404(Chain, name=chain_name, user=request.user)
    chain_requests = chain.requests.all()
    worker_request_list = []
    path = os.path.join(STATICFILES_DIRS[0], 'temp')
    for ch_req in chain_requests:
        worker_request = {'host': ch_req.device_id, 'input_type': ch_req.input_type, 'input_value': ch_req.input_value,
                   'additional_input_value': ch_req.additional_input_value, 'file_path': path}
        worker_request_list.append(worker_request)
    in_memory_zip = send_worker_request_and_zip_result(worker_request_list)
    if in_memory_zip is None:
        return HttpResponse(status_code=200)
    in_memory_zip.seek(0)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=get_response.zip'
    response.write(in_memory_zip.read())
    return response
