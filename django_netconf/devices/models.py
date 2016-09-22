import uuid

from django.db import models


class Device (models.Model):

    """
    Device class.
    Represents network device.

    :attr ip_address
        Is a mandatory upon creation. All other will be set after connection.

    :attr fqdn
        *OPTIONAL* Will be resolved to ip_address if ip_address is not set by a user.
    """

    id = models.UUIDField('Device ID', default=uuid.uuid4, primary_key=True, editable=False)
    ip_address = models.GenericIPAddressField('Devices IP-address:', unique=True)
    name = models.CharField('Device name:', max_length=63, blank=True, editable=False)
    fqdn = models.CharField('Device FQDN:', max_length=63, blank=True)
    platform = models.CharField('Device hardware model:', max_length=50, blank=True, editable=False)
    software_version = models.CharField('Device software version:', max_length=50, blank=True, editable=False)
    serial_number = models.CharField('Device S/N:', max_length=50, blank=True, editable=False)
    up_time = models.CharField('Device ucptime:', max_length=50, blank=True, editable=False)
    last_checked_time = models.DateTimeField('Device last checked time:', editable=False)
    last_checked_status = models.CharField('Device last checked status (UP/DOWN):', max_length=4, editable=False)


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
