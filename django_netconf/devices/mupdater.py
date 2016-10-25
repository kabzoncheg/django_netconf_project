import os
import sys
import logging

from django import setup as django_setup
from django.core.management import settings
from django.core.exceptions import ObjectDoesNotExist


# SCRATCHH!!!!!!!!!!!!!!!!!!!WORKING ON MODELS NOW
def update_model_device(device_ip, facts={}):
    """
    Update Device model with passed facts
    :param device_ip: IP address of Device. CHECK!!! hostname could be passed!!!!
    :param facts: device facts passed as dictionary
    """
    # HERE is relative import issue, beware!
    # Doesn't work from django_netconf.devices.models import Device.
    # Possibly it is a django bug

    if not settings.configured:
        # Adding django_netconf project to sys.path (PATH)
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(project_path)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_netconf.config.settings')
        django_setup()

    from devices.models import Device

    try:
        device_object = Device.objects.get(ip_address=device_ip)
    except ObjectDoesNotExist:
        logger.error('There is no device with IP {} in database!'.format(device_ip))
    else:

        # TEMPRORARY UGLY IMPLEMENTATION:
        if facts == {}:
            device_object.last_checked_status = 'DOWN'
            device_object.save()
            logger.info('device {} changed state to DOWN'.format(device_ip))
            return
        if device_object.name != facts['hostname']:
            device_object.name = facts['hostname']
        if device_object.fqdn != facts['fqdn']:
            device_object.fqdn = facts['fqdn']
        if device_object.platform != facts['model']:
            device_object.platform = facts['model']
        if device_object.software_version != facts['version']:
            device_object.software_version = facts['version']
        if device_object.serial_number != facts['serialnumber']:
            device_object.serial_number = facts['serialnumber']
        if device_object.up_time != facts['RE0']['up_time']:
            device_object.up_time = facts['RE0']['up_time']
        device_object.last_checked_status = 'UP'
        device_object.save()