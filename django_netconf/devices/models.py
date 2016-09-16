from django.db import models


class Device (models.Model):
    name = models.CharField('Device name:', max_length=100)
    ip_addr = models.GenericIPAddressField(primary_key=True, unique=True)
    hostname = models.CharField('hostname', max_length=100, blank=True)