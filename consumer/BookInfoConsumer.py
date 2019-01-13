# -*- coding:utf-8 -*-

import json
import os, sys
sys.path.append(os.getcwd().replace("consumer",""))

from database.IOHandler import FileIO
from database.RabbitMQ import RabbitmqConsumer
from database.RabbitMQ import RabbitmqServer
from configuration.settings import TIME_SLEEP as time_sleep
from configuration.settings import BOOK_INFO_QUEUE_EXCHANGE as book_info_queue_exchange
from configuration.settings import BOOK_INFO_BKUP_QUEUE_EXCHANGE as book_info_bkup_queue_exchange


class BookInfoConsumer(RabbitmqConsumer):
    """
    将rabbitmq服务器中日期的url读取出来进行下一步处理
    """
    def __init__(self, queue, queue_durable=False):
        super(BookInfoConsumer, self).__init__(queue=queue, queue_durable=queue_durable)

    def callback(self, ch, method, properties, body):
        print('[X] get url: %s' % body)
        record = json.loads(body)
        print(json.dumps(record, indent=2))
        message = body.replace("/n","")
        FileIO.writeToFile(text=message, filename="./../data/book_info.json")

        # Backup
        RabbitmqServer.add_message(message=body,
                                   routing_key=book_info_bkup_queue_exchange['routing_key'],
                                   queue=book_info_bkup_queue_exchange['queue'],
                                   queue_durable=book_info_bkup_queue_exchange['queue_durable'],
                                   exchange=book_info_bkup_queue_exchange['exchange'],
                                   exchange_type=book_info_bkup_queue_exchange['exchange_type'])

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print('sleeping...')
        self.connection.sleep(time_sleep*0.05)


if __name__ == '__main__':
    consumer = BookInfoConsumer(
                              queue=book_info_queue_exchange['queue'],
                              queue_durable=book_info_queue_exchange['queue_durable'])
    consumer.start_consuming()