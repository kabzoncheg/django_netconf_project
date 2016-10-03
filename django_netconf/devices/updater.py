import os
import sys
import logging
from time import time
from queue import Queue
from threading import Thread

import django
from django.core.management import settings
from django.core.exceptions import ObjectDoesNotExist
from jnpr.junos import Device

if not settings.configured:
    sys.path.append('/home/django/Programming_projects/django_netconf_project/django_netconf')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_netconf.config.settings')
    django.setup()

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
        raise Exception(_error_msg)


def update_model_device(device_ip, facts):
    """
    Update Device model with passed facts
    :param device_ip: IP address of Device. CHECK!!! hostname could be passed!!!!
    :param facts: device facts passed as dictionary
    """
    print('sdsdsdsdsd')
    from django_netconf.devices.models import Device
    print('agsagagsdgsdg')
    device_object = Device.objects.get(ip_address=device_ip)
    print(device_object)
    #try:
        #device_object = mDevice.objects.get(ip_address=device_ip)
    #except ObjectDoesNotExist:
        #logger.error('There is no device with IP {} in database!'.format(device_ip))
        #print('EXCEPT!')
    #else:
        #pass
        #print(facts)


class DeviceThreadWorker(Thread):
    """
    DeviceThreadworker class
    Provides multithreading support
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
            _dev = Device(host=_host, user=_user, passwd=_password)

            try:
                _dev.open()
            except Exception as _err:
                logger.error('Cannot connet to device {}, error occured: {}'.format(_host, _err))
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
    ts = time()
    thread_number = int(get_env_variable('THRD_NUM'))

    # Create queue for threads
    thread_queue = Queue()
    for x in range(thread_number):
        worker = DeviceThreadWorker(thread_queue)
        # Setting daemon to true will let the main thred exit even if workers are blocking
        worker.daemon = False
        worker.start()

    # Put the tasks into the queue
    for host in host_list:
        logger.info('Queuing in the thread_queue task for host {}'.format(host))
        thread_queue.put((host, tables_to_update))
    thread_queue.join()
    logger.info('Took {}'.format(time() - ts))
    print('Took {}'.format(time() - ts))

if __name__ == '__main__':
    hosts = ['10.0.1.1']
    device_updater(hosts)
