from django.db import models
from django.contrib.auth.models import User

# Same old bug with Import from project root
from devices.models import Device


class Configurations(models.Model):
    name = models.CharField('Configuration name', max_length=100)
    description = models.CharField('Configuration description', max_length=200, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    config = models.CharField('Actual configuration (set or text)', required=True)
