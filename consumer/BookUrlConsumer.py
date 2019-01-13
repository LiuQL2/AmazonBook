# -*-coding:utf-8 -*-

import sys
import os
import json
sys.path.append(os.getcwd().replace("consumer",""))

from configuration.settings import BOOK_URL_QUEUE_EXCHANGE as book_url_queue_exchange
from configuration.settings import USE_PROXY as use_proxy
from configuration.settings import TIME_SLEEP as time_sleep
from database.RabbitMQ import RabbitmqConsumer
from spiders.BookInfoSpider import BookInfoSpider


class BookUrlConsumer(RabbitmqConsumer):
    """
    将rabbitmq服务器中日期的url读取出来进行下一步处理
    """
    def __init__(self, queue, queue_durable=False):
        super(BookUrlConsumer, self).__init__(queue=queue, queue_durable=queue_durable)

    def callback(self, ch, method, properties, body):
        print('[X] get url: %s' % body)
        url_count = json.loads(body)
        book_spider = BookInfoSpider(url_count = url_count ,use_proxy=use_proxy)
        book_spider.parse()#该方法将获得页面url保存到rabbitmq服务器对应的队列中。
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print('sleeping...')
        self.connection.sleep(time_sleep)


if __name__ == '__main__':
    consumer = BookUrlConsumer(
                              queue=book_url_queue_exchange['queue'],
                              queue_durable=book_url_queue_exchange['queue_durable'])
    consumer.start_consuming()