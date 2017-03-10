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

from .forms import UploadConfigForm


logger = logging.getLogger(__name__)


@login_required
def single_set(request):
    return HttpResponse(content='Under development!!!', content_type='text')


@login_required
def configurations_list(request):
    form = UploadConfigForm()
    if request.method == 'POST':
        form = UploadConfigForm(request.POST)
        if form.is_valid():
            config_name = form.cleaned_data['config_name']
            config_description = form.cleaned_data['config_description']
            user = request.user
            config = request.FILES