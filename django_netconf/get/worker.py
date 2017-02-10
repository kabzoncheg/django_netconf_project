# TO DO:
#       Implement Tests,
#       Implement Normal Error handling (error codes),
#       Demonize this module
#   Implement in DeviceThreadWorker Check for file write permissions

import os
import ipaddress
import json
import logging
from queue import Queue
from threading import Thread, Lock
from lxml import etree

import pika
from constance import config

from django_netconf.common.setsettings import set_settings
from django_netconf.devices.jdevice import JunosDevice

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
        self.file_name = None

    def run(self):
        while True:
            # Get IP-address and GET request or cli command from the thread_queue and connect to Device
            host, file_path, input_type, input_value, additional_input_value, mq_chan, mq_prop = self.thread_queue.get()
            usr = config.DEVICE_USER
            pwd = config.DEVICE_PWD
            timeout = config.CONN_TIMEOUT
            dev = JunosDevice(host=host, user=usr, password=pwd, db_flag=True, auto_probe=timeout)
            try:
                logger.info('Connecting to Device {}'.format(host))
                dev.connect()
            except Exception as err:
                logger.error('Failed to connect to Device {}'.format(host))
                self.err = err
                self.status_code = 1
            else:
                dev_request = None
                logger.info('Executing {} request {} with additional '
                            'parameters {} on Device {}'.format(input_type, input_value, additional_input_value, host))
                try:
                    if input_type == 'xml':
                        dev_request = dev.xml(input_value)
                    elif input_type == 'rpc':
                        dev_request = dev.rpc(input_value, additional_input_value)
                    elif input_type == 'cli':
                        dev_request = dev.cli(input_value)
                    else:
                        self.err = "input_type configured improperly!" \
                                   " must be 'xml', 'cli' or 'rpc', but got {}".format(input_type)
                        self.status_code = 400
                        logger.error(self.err)
                except Exception as err:
                    self.err = err
                    self.status_code = 400
                else:
                    if isinstance(dev_request, etree._Element):
                        et = etree.ElementTree(dev_request)
                        self.file_name = mq_prop.correlation_id + '.xml'
                        et.write(os.path.join(file_path, self.file_name))
                    else:
                        self.file_name = mq_prop.correlation_id + '.txt'
                        with open(os.path.join(file_path, self.file_name), 'w+') as file:
                            file.write(dev_request)
                finally:
                    logger.info('Closing connection with Device {}'.format(host))
                    dev.disconnect()
            finally:
                if self.err:
                    self.file_name = mq_prop.correlation_id + '.txt'
                    with open(os.path.join(file_path, self.file_name), 'w+') as file:
                        file.write('\t======ERROR======\n')
                        file.write(str(self.err))
                self.lock.acquire()
                self.callback(host, self.status_code, mq_chan, mq_prop, self.file_name, self.err)
                self.lock.release()
                self.thread_queue.task_done()


def callback(host, status_code, mq_chan, mq_prop, file_name, err=None):
    # Callback for thread. Generates RabbitMQ rpc response
    response = json.dumps({'host': host, 'status_code': status_code, 'file_name': file_name})
    if mq_prop.reply_to and mq_prop.correlation_id:
        mq_chan.basic_publish(exchange='', routing_key=mq_prop.reply_to,
                              properties=pika.BasicProperties(correlation_id=mq_prop.correlation_id), body=response)
    if not err:
        logger.info('GET Request successfull for host {}'.format(host))
    else:
        logger.error('GET Request to host {} FAILED, error occured: {}'.format(host, err))

# set Django settings
set_settings()

# Set up connection to RabbitMQ server and queue declaration
mq_connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue='get_requests', durable=True, arguments={'x-message-ttl': 60000})

# Queue for thread tasks
thread_queue = Queue()
lock = Lock()

# TO CONSIDER. Additional number of threads for GET requests
for num in range(config.THREAD_NUM):
    worker = DeviceThreadWorker(thread_queue, lock, callback)
    # Setting worker.daemon to True will let the main thread exit even if workers are blocking
    worker.daemon = True
    worker.start()


def mq_method(channel, method, properties, body):
    # Strange, recieving json string from RabbitMQ queue as bytes
    # Possible it is a bug
    logger.info('Received data {} on RabbitMQ channel {}'.format(body, channel))
    if isinstance(body, bytes):
        json_data = body.decode('utf-8')
    else:
        json_data = body
    try:
        # Each of the statements below could drop one or serveral errors
        # For example ipaddress.ip_address(host) could drop ValueError if ip-address is not correct
        # For future work
        data = json.loads(json_data)
        host = data['get_request']['host']
        input_type = data['get_request']['input_type']
        input_value = data['get_request']['input_value']
        additional_input_value = data['get_request']['additional_input_value']
        file_path = data['get_request']['file_path']
        ipaddress.ip_address(host)
    except Exception as err:
        logger.error('Unable to parse data: {}, got Exception: {}'.format(json_data, err))
    else:
        logger.info('Queuing in the thread_queue GET request task {} for host {}'.format(data, host))
        thread_queue.put((host, file_path, input_type, input_value, additional_input_value, channel, properties))

mq_channel.basic_consume(mq_method, queue='get_requests', no_ack=True)
mq_channel.start_consuming()
