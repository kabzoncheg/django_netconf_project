# TO DO: Implement signal handling for dynamic settings (django-constance),
#       Implement Tests,
#       Implement Normal Error handling (error codes),
#       Demonize this module

import json
import logging
import os
import sys

import pika
import ipaddress
from queue import Queue
from threading import Thread, Lock

from django.core.management import settings
from django import setup as django_setup
from constance import config

from django_netconf.devices.jdevice import JunosDevice
from django_netconf.devices.mupdater import ModelUpdater


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
    def __init__(self, thread_queue, lock, callback):
        Thread.__init__(self)
        self.thread_queue = thread_queue
        self.lock = lock
        self.callback = callback
        self.err = None
        self.status_code = 0

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
                self.callback(host, self.status_code, self.err)
                self.lock.release()
                self.thread_queue.task_done()

def callback(host, status_code, err=None):
    if not err:
        logger.info('Update successfull for host {}'.format(host))
    else:
        logger.error('Cannot update host {}, error occured: {}'.format(host, err))


_settings_setter()

# Set up connection to RabbitMQ server and queue declaration
mq_connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue='db_update', durable=True, arguments={'x-message-ttl': 60000})

thread_queue = Queue()
lock = Lock()

for num in range(config.THREAD_NUM):
    worker = DeviceThreadWorker(thread_queue, lock, callback)
    # Setting daemon to True will let the main thread exit even if workers are blocking
    worker.daemon = True
    worker.start()


def mq_method(channel, method, properties, body):
    # Strange, recieving json string from RabbitMQ queue as bytes
    # Possible it is a bug
    if isinstance(body,bytes):
        json_data = body.decode('utf-8')
    else:
        json_data = body
    try:
        # Each of the statements below could drop one or serveral errors
        # For example ipaddress.ip_address(host) could drop ValueError if ip-address is not correct
        # For future work
        data = json.loads(json_data)
        host = data['db_update']['host']
        ipaddress.ip_address(host)
    except Exception as err:
        logger.error('Unable to parse data: {}, got Exception: {}'.format(data, err))
    else:
        logger.info('Queuing in the thread_queue task for host {}'.format(host))
        thread_queue.put(host)

mq_channel.basic_consume(mq_method, queue='db_update', no_ack=True)
mq_channel.start_consuming()