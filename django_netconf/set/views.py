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
from .forms import UploadConfigForm


logger = logging.getLogger(__name__)


@login_required
def single_set(request):
    return HttpResponse(content='Under development!!!', content_type='text')


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
            duplicate_file_names =[]
            for config in configs:
                instance = Configurations(name=config.name, description=config_description,
                                          mime_type=config.content_type, user=user, config=config)
                try:
                    instance.save()
                except IntegrityError:
                    duplicate_file_names.append(config.name)
            if duplicate_file_names:
                error = 'File(s) with folowing name(s) {} already exist(s)!'.format(duplicate_file_names)
            print(error)
    return render(request, 'set/configurations.html', {'form': form, 'configurations_list': configurations_list,
                                                       'error': error})
