from django.db import models
from django.contrib.auth.models import User

# Same old bug with Import from project root
from devices.models import Device

INPUT_TYPE = (
    ('xml', 'raw XML'),
    ('rpc', 'RPC on demand'),
    ('cli', 'CLI  show command'),
)


class Request(models.Model):
    # Rename to GetRequest
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    input_type = models.CharField('Request type', max_length=3, choices=INPUT_TYPE)
    input_value = models.CharField('Actual request data', max_length=1000)
    additional_input_value = models.CharField('Additional request data, only for rpc request',
                                              max_length=200, blank=True)


class Chain(models.Model):
    # Rename to GetChain
    name = models.CharField('GET chain name:', max_length=100)
    description = models.CharField('GET chain description', max_length=200, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requests = models.ManyToManyField(Request)
