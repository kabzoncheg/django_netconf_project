# TO DO: Implement signal handling for dynamic settings (django-constance),
#       Implement Tests,
#       Implement Normal Error handling (error codes),
#       Demonize this module

import json
import logging
import ipaddress
from queue import Queue
from threading import Thread, Lock

import pika
from constance import config
import django

from django_netconf.devices.jdevice import JunosDevice
from django_netconf.devices.mupdater import ModelUpdater
from django_netconf.common.setsettings import set_settings


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
            host, mq_chan, mq_prop = self.thread_queue.get()
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
                self.status_code = 1
            else:
                # It is possible to get KeyError here if meth_tuple improperly configured in jdevice.py
                junos_dev_meth_names = dev.all_get_methods()
                for meth_name in junos_dev_meth_names:
                    data = getattr(dev, meth_name)()
                    try:
                        ModelUpdater(data, host=host).updater()
                    except Exception as err:
                        self.err = err
                        self.status_code = 2
                dev.disconnect()
            finally:
                django.db.connection.close()
                self.lock.acquire()
                self.callback(host, self.status_code, mq_chan, mq_prop, self.err)
                self.lock.release()
                self.thread_queue.task_done()


def callback(host, status_code, mq_chan, mq_prop, err=None):
    response = json.dumps({'host': host, 'status_code': status_code})
    if mq_prop.reply_to and mq_prop.correlation_id:
        mq_chan.basic_publish(exchange='', routing_key=mq_prop.reply_to,
                              properties=pika.BasicProperties(correlation_id=mq_prop.correlation_id), body=response)
    if not err:
        logger.info('Update successfull for host {}'.format(host))
    else:
        logger.error('Cannot update host {}, error occured: {}'.format(host, err))

# set Django settings
set_settings()

# Set up connection to RabbitMQ server and queue declaration
mq_connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue='db_update', durable=True, arguments={'x-message-ttl': 60000})

# Queue for thread tasks
thread_queue = Queue()
lock = Lock()

for num in range(config.THREAD_NUM):
    worker = DeviceThreadWorker(thread_queue, lock, callback)
    # Setting worker.daemon to True will let the main thread exit even if workers are blocking
    worker.daemon = True
    worker.start()


def mq_method(channel, method, properties, body):
    # Strange, recieving json string from RabbitMQ queue as bytes
    # Possible it is a bug
    if isinstance(body, bytes):
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
        logger.error('Unable to parse data: {}, got Exception: {}'.format(json_data, err))
    else:
        logger.info('Queuing in the thread_queue task for host {}'.format(host))
        thread_queue.put((host, channel, properties))

mq_channel.basic_consume(mq_method, queue='db_update', no_ack=True)
mq_channel.start_consuming()
