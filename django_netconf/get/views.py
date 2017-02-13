import logging
import os
import zipfile
from io import BytesIO

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from django_netconf.common.workertasks import multiple_get_request
from django_netconf.config.settings import STATICFILES_DIRS

from .forms import SingleGETRequestForm


logger = logging.getLogger(__name__)


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
            file_names = multiple_get_request([request])
            if file_names is None:
                return HttpResponse(status_code=200)
            else:
                pass
            in_memory = BytesIO()
            zip_archive = zipfile.ZipFile(in_memory, mode='w')
            for file_name in file_names:
                file_path = os.path.join(path, file_name)
                try:
                    with open(file_path) as f:
                        file_content = f.read()
                    logger.info('Writing file at {} to in memory archive:', file_path.format(file_path))
                    zip_archive.writestr(file_name, file_content)
                except RuntimeError:
                    logger.info('Got ERROR while writing file at {} to in memory archive:', file_path)
                    zip_archive.close()
                finally:
                    logger.info('removing file {}:', file_path)
                    os.remove(file_path)
            zip_archive.close()
            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=get_response.zip'
            in_memory.seek(0)
            response.write(in_memory.read())
            return response
    else:
        return render(request, 'get/index.html', {'form': form})
