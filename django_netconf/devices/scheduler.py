import json
import logging
import time

import pika
from constance import config

from django_netconf.common.setsettings import set_settings

# set Django settings before importing model
set_settings()
from devices.models import Device

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

while True:
    devices = Device.objects.all()
    for dev in devices:
        host = dev.ip_address
        manual_update_flag = False
        message_as_dict = {'db_update': {'host':host, 'manual_update_flag': manual_update_flag}}
        message = json.dumps(message_as_dict, sort_keys=True)
        channel.basic_publish(exchange='', routing_key='db_update', body=message)
        logger.info('Message {} sent to RabbitMQ exchange'.format(message))
    logger.info('Sleeping for {} seconds'.format(config.POLL_TIME))
    time.sleep(config.POLL_TIME)

connection.close()
