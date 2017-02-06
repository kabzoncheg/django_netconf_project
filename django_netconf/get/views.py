import os
import logging

from django.shortcuts import render
from constance import config

from django_netconf.common.jdevice import JunosDevice
from django_netconf.common.zip import zipper
from .forms import SingleGETRequestForm

logger = logging.getLogger(__name__)

def single_get(request):
    form = SingleGETRequestForm()
    if request.method == 'POST':
        form = SingleGETRequestForm(request.POST)
        if form.is_valid():
            usr = config.DEVICE_USER
            pwd = config.DEVICE_PWD
            timeout = config.CONN_TIMEOUT
            ip_addr = form.cleaned_data['ip_address']
            input_type = form.cleaned_data['input_type']
            input_value = form.cleaned_data['input_value']
            additional_input_value = form.cleaned_data['additional_input_value']
            print(usr, pwd)
            device = JunosDevice(host=ip_addr, user=usr, password=pwd, auto_probe=timeout)
            try:
                device.connect()
            except Exception as err:
                logger.error('Tried connect to {}, but failed with {}'.format(ip_addr, err))
                error_text = 'Unable to connect to: {}'.format(ip_addr)
                return render(request, 'get/index.html', {'error': error_text, 'form': form})
            # TO DO: Try block here
            if input_type == 'xml':
                dev_request = device.xml(input_value)
            elif input_type == 'rpc':
                dev_request = device.rpc(input_value, additional_input_value)
            elif input_type == 'cli':
                dev_request = device.cli(input_value)
            device.disconnect()
            return render(request, 'get/index.html', {'response': dev_request, 'form': form})
    else:
        return render(request, 'get/index.html', {'form': form})

