import uuid

from django.db import models


class Device (models.Model):
    """
    Device class.
    Represents network device.

    :attr ip_address
        Is a mandatory upon creation. All other will be set after connection.
        if fqdn is set instead of ip_address, it will be resolved upon form verification

    :attr fqdn
        *OPTIONAL* Will be resolved to ip_address if ip_address is not set by a user.
    """
    ip_address = models.GenericIPAddressField('Devices management IP-address:', primary_key=True,)
    description = models.CharField('Device description', max_length=300, blank=True)
    name = models.CharField('Device name:', max_length=63, blank=True, editable=False)
    fqdn = models.CharField('Device FQDN:', max_length=63, blank=True)
    model = models.CharField('Device hardware model:', max_length=50, blank=True, editable=False)
    version = models.CharField('Device software version:', max_length=50, blank=True, editable=False)
    serialnumber = models.CharField('Device S/N:', max_length=50, blank=True, editable=False)
    up_time = models.CharField('Device uptime:', max_length=50, blank=True, editable=False)
    two_re = models.BooleanField('Device has 2 RE (True/False)',blank=True, editable=False)
    last_checked_time = models.DateTimeField('Device last checked time:', auto_now=True, editable=False)
    last_checked_status = models.BooleanField('True for UP, False for DOWN:', editable=False)


class DeviceInstance(models.Model):
    """
    DeviceInstance class.
    Represents devices routing instance
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    instance_name = models.CharField(max_length=100, editable=False, primary_key=True)
    instance_type = models.CharField(max_length=30, editable=False)
    router_id = models.GenericIPAddressField(editable=False)
    instance_state = models.CharField(max_length=30, editable=False)


class InstanceArpTable:
    related_instance = models.ForeignKey(DeviceInstance, on_delete=models.CASCADE)
    mac_address = models.CharField(max_length=17, editable=False)
    ip_address = models.GenericIPAddressField(editable=False)
    interface_name = models.CharField(max_length=100, editable=False)
    hostname = models.CharField(max_length=100, editable=False, primary_key=True)


def device_config_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/configs/device_<id>/filename
    return 'configs/device_{0}/{1}'.format(instance.related_device_id, filename)


class DeviceConfig (models.Model):

    """
    Device Configuration class.
    Represents configuration files for each device
    """

    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    upload_path = models.FileField(upload_to=device_config_path)
    upload_time = models.DateTimeField(editable=False, auto_now=True)
