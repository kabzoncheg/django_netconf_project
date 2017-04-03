# TO DO:
#       Implement Tests,
#       Implement Normal Error handling (error codes)
#       Demonize this module
#   Implement in SetThreadWorker Check for file write permissions

import os
import ipaddress
import json
import logging
from queue import Queue
from threading import Thread
from threading import Lock
from lxml import etree

import pika
from constance import config
from jnpr.junos import Device as JunosDevice
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import CommitError
from jnpr.junos.exception import ConfigLoadError
from django.core.exceptions import ObjectDoesNotExist

from django_netconf.common.setsettings import set_settings

logger = logging.getLogger(__name__)


class SetThreadWorker(Thread):
    """
    SetThreadWorker class
    Provides multithreading support for multiple SSH-agents
    """
    def __init__(self, thread_queue, lock, callback, logger):
        Thread.__init__(self)
        self.thread_queue = thread_queue
        self.lock = lock
        self.callback = callback
        self.logger = logger
        file_name = None

    def run(self):
        while True:
            # Get IP-address and SET request  from the thread_queue and connect to Device
            host, file_path, config_id, compare_flag, mq_chan, mq_prop = self.thread_queue.get()
            usr = config.DEVICE_USER
            pwd = config.DEVICE_PWD
            timeout = config.CONN_TIMEOUT
            dev = JunosDevice(host=host, user=usr, password=pwd, auto_probe=timeout)
            error = None
            status_code = 0
            file_name = None
            result = ''
            try:
                self.logger.info('Connecting to Device {}'.format(host))
                dev.open(gather_facts=False)
            except Exception as err:
                self.logger.error('Failed to connect to Device {}'.format(host))
                error = err
                status_code = 1
            else:
                try:
                    config_file = Configurations.objects.get(id=config_id).config.read().decode('ascii')
                except ObjectDoesNotExist:
                    self.logger.error('Configurations object with id {} does not exist in database'.format(config_id))
                    error = 'Configurations object with id {} was deleted'.format(config_id)
                    status_code = 404
                else:
                    self.logger.info('Loading configuration\n {}\n on Device {}'.format(config_file, host))
                    with Config(dev) as confdev:
                        try:
                            confdev.load(config_file)
                            if compare_flag:
                                self.logger.info('COMPARE configuration\n {}\n on Device {}'.format(config_file, host))
                                result = confdev.diff()
                                confdev.rollback()
                            else:
                                confdev.commit()
                                self.logger.info('COMMIT configuration\n {}\n on Device {}'.format(config_file, host))
                                result = 'COMMIT on Device {} SUCCESSFUL'.format(host)
                        except ConfigLoadError as err:
                            confdev.rollback()
                            self.logger.error('Load configuration\n {}\n FAILED on Device {}'.format(config_file, host))
                            error = err
                            status_code = 201
                        except CommitError as err:
                            confdev.rollback()
                            self.logger.error('Commit configuration\n {}\n FAILED '
                                              'on Device {}'.format(config_file, host))
                            error = err
                            status_code = 202
                        except Exception as err:
                            confdev.rollback()
                            self.logger.critical('Unknown error {}'. format(err))
                            error = err
                            status_code = 200

                finally:
                    self.logger.info('Closing connection with Device {}'.format(host))
                    dev.close()
            finally:
                file_name = mq_prop.correlation_id + '-' + host + '.txt'
                with open(os.path.join(file_path, file_name), 'w+') as file:
                    if error:
                        file.write('==========ERROR==========\n')
                        file.write(str(error))
                    elif result:
                        file.write('=========SUCCESS=========\n')
                        file.write('======CONFIGURATION======\n')
                        file.write(config_file)
                        file.write('\n========RESULT=========\n')
                        file.write(str(result))
                self.lock.acquire()
                self.callback(host, status_code, mq_chan, mq_prop, file_name, error)
                self.lock.release()
                self.thread_queue.task_done()


def callback(host, status_code, mq_chan, mq_prop, file_name, err=None):
    # Callback for thread. Generates RabbitMQ rpc response
    response = json.dumps({'host': host, 'status_code': status_code, 'file_name': file_name})
    if mq_prop.reply_to and mq_prop.correlation_id:
        mq_chan.basic_publish(exchange='', routing_key=mq_prop.reply_to,
                              properties=pika.BasicProperties(correlation_id=mq_prop.correlation_id), body=response)
    if not err:
        logger.info('SET Request successfull for host {}'.format(host))
    else:
        logger.error('SET Request to host {} FAILED, error occurred: {}'.format(host, err))

# set Django settings
set_settings()
from set.models import Configurations

# Set up connection to RabbitMQ server and queue declaration
mq_connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue='set_requests', durable=True, arguments={'x-message-ttl': 60000})

# Queue for thread tasks
thread_queue = Queue()
lock = Lock()

# TO CONSIDER. Additional number of threads for SET requests
for num in range(config.THREAD_NUM):
    worker = SetThreadWorker(thread_queue, lock, callback, logger)
    # Setting worker.daemon to True will let the main thread exit even if workers are blocking
    worker.daemon = True
    worker.start()


def mq_method(channel, method, properties, body):
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
        host = data['set_request']['host']
        config_id = data['set_request']['config_id']
        file_path = data['set_request']['file_path']
        compare_flag = data['set_request']['compare_flag']
        ipaddress.ip_address(host)
    except Exception as err:
        logger.error('Unable to parse data: {}, got Exception: {}'.format(json_data, err))
    else:
        logger.info('Queuing in the thread_queue GET request task {} for host {}'.format(data, host))
        thread_queue.put((host, file_path, config_id, compare_flag, channel, properties))

mq_channel.basic_consume(mq_method, queue='set_requests', no_ack=True)
mq_channel.start_consuming()
