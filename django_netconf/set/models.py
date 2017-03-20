from django.db import models
from django.contrib.auth.models import User

from devices.models import Device


def device_config_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/configs/user_<id>/filename
    return 'configs/device_{0}/{1}'.format(instance.user.id, filename)


class Configurations(models.Model):
    # Rename to Configuration
    name = models.CharField('Configuration name', max_length=100)
    description = models.CharField('Configuration description', max_length=200, default=None)
    mime_type = models.CharField('MIME Type', max_length=100, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    config = models.FileField(upload_to=device_config_path)

    class Meta:
        unique_together = ('name', 'user')


class SetRequest(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    config = models.ForeignKey(Configurations, on_delete=models.CASCADE)


class SetChain(models.Model):
    name = models.CharField('SET chain name:', max_length=100)
    description = models.CharField('SET chain description', max_length=200, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requests = models.ManyToManyField(SetRequest)
