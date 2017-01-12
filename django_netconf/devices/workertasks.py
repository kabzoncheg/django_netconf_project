import json
import uuid
import logging
from time import time

import pika

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SendRPC(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.time_smpl = time()
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='db_update',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(n))
        while self.response is None:
            # In a case of worker daemon cannot process our request
            # run timer for 10 sec
            self.connection.process_data_events()
            if  time() - self.time_smpl < 10:
                pass
            else:
                self.response = {'status_code': 200}
                break
        return self.response


def rpc_update(host):
    # Performs synchronous RabbitMQ RPC request to worker daemon
    # returns status code of operation
    trans_id = uuid.uuid1().int
    manual_update_flag = True
    message_as_dict = {'db_update': {'host':host, 'transaction_id': trans_id, 'manual_update_flag': manual_update_flag}}
    message = json.dumps(message_as_dict, sort_keys=True)
    rpc_sender = SendRPC()
    logger.info('Message {} sent to RabbitMQ exchange'.format(message))
    response = rpc_sender.call(message)
    logger.info('Responce {} received for Message {}'.format(message, response))
    if isinstance(response, bytes):
        json_data = response.decode('utf-8')
    else:
        json_data = response
    result = json.loads(json_data)
    status_code = result['status_code']
    return status_code


