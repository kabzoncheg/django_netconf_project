# TO DO: Implement signal handling ofr dynamic settings (django-constance),
#       Callbacks for threads!
#       Tests, Normal Error handling

import os
import sys
import logging
from time import time
from queue import Queue
from threading import Thread

from django_netconf.devices.jdevice import JunosDevice
from django_netconf.devices.mupdater import ModelUpdater
from django.core.management import settings
from django import setup as django_setup
from constance import config


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _settings_setter():
    """
    Adds django_netconf project to sys.path (PATH) if it is not already there

    :return: None
    """
    if not settings.configured:
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(project_path)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_netconf.config.settings')
        django_setup()


class DeviceThreadWorker(Thread):
    """
    DeviceThreadworker class
    Provides multithreading support for multiple SSH-agents
    """
    def __init__(self, thread_queue):
        Thread.__init__(self)
        self.thread_queue = thread_queue

    def run(self):
        while True:
            # Get IP-address from the thread_queue and connect to Device
            host = self.thread_queue.get()
            usr = config.DEVICE_USER
            pwd = config.DEVICE_PWD
            timeout = config.CONN_TIMEOUT
            dev = JunosDevice(host=host, user=usr, password=pwd, db_flag=True, auto_probe=timeout)
            try:
                dev.connect()
            except Exception as err:
                logger.error('Cannot connet to device {}, error occured: {}'.format(host, err))
                data = ([{'last_checked_status': False}], 'Device')
                ModelUpdater(data, host=host).updater()
            else:
                # It is possible to get KeyError here if meth_tuple improperly configured
                # in jdevice.py, so it will kill worker.py, as planned
                junos_dev_meth_names = dev.all_get_methods()
                for meth_name in junos_dev_meth_names:
                    data = getattr(dev, meth_name)()
                    try:
                        ModelUpdater(data, host=host).updater()
                    except Exception as err:
                        logger.error('Cannot update ModelUpdater instance for host {} with data{}'
                                     'thread exited with {}'.format(host, data, err))
                dev.disconnect()
            finally:
                self.thread_queue.task_done()


def device_updater(host_list):
    """
    :param host_list: Must be a list of strings, containing IP-addresses! IMPLEMENT CHECK!
    :return: None
    """
    _settings_setter()
    ts = time()

    thread_queue = Queue()
    for num in range(config.THREAD_NUM):
        worker = DeviceThreadWorker(thread_queue)
        # Setting daemon to true will let the main thred exit even if workers are blocking
        worker.daemon = True
        worker.start()

    for host in host_list:
        logger.info('Queuing in the thread_queue task for host {}'.format(host))
        thread_queue.put(host)
    # Waiting for a queue for task completion
    thread_queue.join()
    logger.info('Took {}'.format(time() - ts))
    print('Took {}'.format(time() - ts))

if __name__ == '__main__':
    real_hosts = ['10.0.1.1', '10.0.3.2']
    fake_hosts = []
    for x in range(1, 50):
        entry = '10.192.172.' + str(x)
        fake_hosts.append(entry)
    hosts = real_hosts + fake_hosts
    device_updater(fake_hosts)
