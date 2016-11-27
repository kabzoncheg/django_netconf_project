# TO DO: Implement signal handling ofr dynamic settings (django-constance),
#       Callbacks for threads!
#       Tests, Normal Error handling

import os
import sys
import logging
# from time import time
import ipaddress
from queue import Queue
from threading import Thread, Lock

from django_netconf.devices.jdevice import JunosDevice
from django_netconf.devices.mupdater import ModelUpdater
from django.core.management import settings
from django import setup as django_setup
from constance import config


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
task_counter = callback_counter = 0


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
    def __init__(self, thread_queue, lock, callback, errback):
        Thread.__init__(self)
        self.thread_queue = thread_queue
        self.lock = lock
        self.callback = callback
        self.errback = errback
        self.err = None

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
                data = ([{'last_checked_status': False}], 'Device')
                ModelUpdater(data, host=host).updater()
                self.err = err
            else:
                # It is possible to get KeyError here if meth_tuple improperly configured in jdevice.py
                junos_dev_meth_names = dev.all_get_methods()
                for meth_name in junos_dev_meth_names:
                    data = getattr(dev, meth_name)()
                    try:
                        ModelUpdater(data, host=host).updater()
                    except Exception as err:
                        self.err = err
                dev.disconnect()
            finally:
                self.lock.acquire()
                if self.err:
                    self.errback(host, self.err)
                else:
                    self.callback(host)
                self.lock.release()
                self.thread_queue.task_done()


def callback(host):
    global callback_counter
    callback_counter += 1
    logger.info('Update successfull for host {}'.format(host))


def errback(host, err):
    global callback_counter
    callback_counter += 1
    logger.error('Cannot update host {}, error occured: {}'.format(host, err))


def device_updater():
    """
    Testing with user input. Next step - RabitMq
    :param host_list: Must be a list of strings, containing IP-addresses! IMPLEMENT CHECK!
    :return: None
    """
    _settings_setter()

    thread_queue = Queue()
    lock = Lock()
    for num in range(config.THREAD_NUM):
        worker = DeviceThreadWorker(thread_queue, lock, callback, errback)
        # Setting daemon to True will let the main thread exit even if workers are blocking
        worker.daemon = True
        worker.start()

    while True:
        host = input('Enter IP-address:')
        try:
            ipaddress.ip_address(host)
        except ValueError as err:
            logger.error(err)
        else:
            logger.info('Queuing in the thread_queue task for host {}'.format(host))
            thread_queue.put(host)


if __name__ == '__main__':
    # real_hosts = ['10.0.1.1', '10.0.3.2']
    # fake_hosts = []
    # for x in range(1, 10):
    #     entry = '10.192.172.' + str(x)
    #     fake_hosts.append(entry)
    # hosts = real_hosts + fake_hosts
    # device_updater(hosts)
    device_updater()