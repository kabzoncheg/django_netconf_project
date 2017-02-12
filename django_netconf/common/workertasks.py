import json
import uuid
import logging
from time import time
from queue import Queue
from threading import Thread, Lock

import pika

logging.basicConfig(level='INFO', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SendRPC:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, msg, mq_routing_key, sleep_time=30):
        self.time_smpl = time()
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=mq_routing_key,
                                   properties=pika.BasicProperties(
                                         reply_to=self.callback_queue,
                                         correlation_id=self.corr_id,
                                         ),
                                   body=str(msg))
        while self.response is None:
            # In a case of worker daemon cannot process our request
            # run timer for slee_time sec
            self.connection.process_data_events()
            if time() - self.time_smpl < sleep_time:
                pass
            else:
                self.response = {'status_code': 200}
                logger.warning('RPC request for message {} timed out'.format(msg))
                break
        return self.response


class _MultipleGetRequestThreader(Thread):
    def __init__(self, thread_queue, lock, file_name_list):
        Thread.__init__(self)
        self.thread_queue = thread_queue
        self.lock = lock
        self.file_name_list = file_name_list

    def run(self):
        while True:
            message = self.thread_queue.get()
            logger.info('Got message {} from the Thread queue'.format(message))
            rpc_sender = SendRPC()
            logger.info('Message {} sent to RabbitMQ exchange'.format(message))
            response = rpc_sender.call(message, mq_routing_key='get_requests', sleep_time=20)
            logger.info('Responce {} received for Message {}'.format(response, message))
            if isinstance(response, bytes):
                json_data = response.decode('utf-8')
                result = json.loads(json_data)
            elif isinstance(response, dict):
                result = response
            else:
                json_data = response
                result = json.loads(json_data)
            status_code = result['status_code']
            if status_code == 0:
                file_name = result['file_name']
                self.lock.acquire()
                self.file_name_list.append(file_name)
                self.lock.release()
            else:
                logger.error('Request {} finished with error (status code = {}'. format(message, status_code))
            self.thread_queue.task_done()


def rpc_update(host):
    # Performs synchronous RabbitMQ RPC request to devices.worker daemon
    # returns status code of operation
    # REMOVE UUID!
    trans_id = uuid.uuid1().int
    manual_update_flag = True
    message_as_dict = {'db_update': {'host': host, 'transaction_id': trans_id,
                                     'manual_update_flag': manual_update_flag}}
    message = json.dumps(message_as_dict, sort_keys=True)
    rpc_sender = SendRPC()
    logger.info('Message {} sent to RabbitMQ exchange'.format(message))
    response = rpc_sender.call(message, mq_routing_key='db_update', sleep_time=60)
    logger.info('Responce {} received for Message {}'.format(response, message))
    if isinstance(response, bytes):
        json_data = response.decode('utf-8')
        result = json.loads(json_data)
    elif isinstance(response, dict):
        result = response
    else:
        json_data = response
        result = json.loads(json_data)
    status_code = result['status_code']
    logger.info('Returning status code {}'.format(status_code))
    return status_code


def multiple_get_request_async_rpc_call(get_requests):
    # Performs asynchronous RabbitMQ RPC requests to get.worker daemon
    if isinstance(get_requests, list):
        pass
    else:
        raise TypeError
    file_name_list = []
    thread_queue = Queue()
    lock = Lock()
    for num in range(len(get_requests)):
        worker = _MultipleGetRequestThreader(thread_queue, lock, file_name_list)
        worker.daemon = True
        worker.start()
    for request in get_requests:
        message_as_dict = {'get_request': {'host': request['host'], 'input_type': request['input_type'],
                                           'input_value': request['input_value'],
                                           'additional_input_value': request['additional_input_value'],
                                           'file_path': request['file_path']}}
        message = json.dumps(message_as_dict, sort_keys=True)
        thread_queue.put(message)
    thread_queue.join()
    print(file_name_list)


if __name__ == '__main__':
    # While normal tests nor implemented:
    host1 = '10.0.1.1'
    host2 = '10.0.3.2'
    inp_cli = 'show route'
    inp_xml = '<get-arp-table-information>' \
                '    <no-resolve/>' \
                 '    <vpn>default</vpn>' \
                 '</get-arp-table-information>'
    inp_rpc = 'get_interface_information'
    add_inp = r"{'terse': True}"

    corrupted_cli = 'show pika-chu'
    corrupted_xml = '<get-pika-chu></get-pika-chu>'
    corrupted_rpc = 'get_pika_chu'

    path = '/home/django/Programming_projects/django_netconf_project/sample_code/test/'

    get_req_1 = {'host': host1, 'input_type': 'cli', 'input_value': inp_cli, 'additional_input_value': None,
                 'file_path': path}
    get_req_2 = {'host': host2, 'input_type': 'xml', 'input_value': inp_xml, 'additional_input_value': None,
                 'file_path': path}

    multiple_get_request_async_rpc_call([get_req_1, get_req_2])