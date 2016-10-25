import os
import sys
import logging
from time import time
from queue import Queue
from threading import Thread

from django import setup as django_setup
from django.core.management import settings
from django.core.exceptions import ObjectDoesNotExist
from jnpr.junos import Device as device_connector

# In case this module run outside of django
if not settings.configured:
    # Adding django_netconf project to sys.path (PATH)
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_netconf.config.settings')
    django_setup()

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_env_variable(var_name):
    """
    Get the environment variable or return exception
    """
    try:
        return os.environ[var_name]
    except KeyError:
        _error_msg = "Set the {} environment variable!".format(var_name)
        logger.error(_error_msg)
        raise Exception(_error_msg)


def update_model_device(device_ip, facts={}):
    """
    Update Device model with passed facts
    :param device_ip: IP address of Device. CHECK!!! hostname could be passed!!!!
    :param facts: device facts passed as dictionary
    """
    # HERE is relative import issue, beware!
    # Doesn't work from django_netconf.devices.models import Device.
    # Possibly it is a django bug
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
        logger.info('fineshed updating model {}'.format(Device))


class DeviceThreadWorker(Thread):
    """
    DeviceThreadworker class
    Provides multithreading support for multiple SSH-agents
    """
    def __init__(self, thread_queue):
        Thread.__init__(self)
        self._thread_queue = thread_queue

    def run(self):
        while True:
            # Get hostname or IP-address from the thread_queue and connect to Device
            _host, _tables_to_update = self._thread_queue.get()
            _user = get_env_variable('JNPR_USR')
            _password = get_env_variable('JNPR_PWD')
            _dev = device_connector(host=_host, user=_user, passwd=_password)

            try:
                _dev.open()
            except Exception as _err:
                logger.error('Cannot connet to device {}, error occured: {}'.format(_host, _err))
                update_model_device(_host, facts={})

                # Necessary Models update operations performed here
            else:
                if 'arp-table' in _tables_to_update:
                    # TO MAKE: get-arp-table-information
                    pass
                if 'int-info' in _tables_to_update:
                    # TO MAKE; get-interface-information
                    pass
                if 'route-info' in _tables_to_update:
                    # TO MAKE: get-route-inforamtion
                    pass
                _facts = _dev.facts
                update_model_device(_host, _facts)
                _dev.close()
            finally:
                self._thread_queue.task_done()


def device_updater(host_list, tables_to_update=()):
    """
    :param host_list: Must be a list of strings, containing IP-addresses! IMPLEMENT CHECK!
    :param tables_to_update: must be a tuple of strings with names of tables! IMPLEMENT CHECK!
    :return: None
    """
    ts = time()
    thread_number = int(get_env_variable('THRD_NUM'))

    thread_queue = Queue()
    for x in range(thread_number):
        worker = DeviceThreadWorker(thread_queue)
        # Setting daemon to true will let the main thred exit even if workers are blocking
        worker.daemon = True
        worker.start()

    for host in host_list:
        logger.info('Queuing in the thread_queue task for host {}'.format(host))
        thread_queue.put((host, tables_to_update))
    thread_queue.join()
    logger.info('Took {}'.format(time() - ts))
    print('Took {}'.format(time() - ts))

if __name__ == '__main__':
    hosts = ['10.0.1.1', '10.0.1.2']
    device_updater(hosts)
