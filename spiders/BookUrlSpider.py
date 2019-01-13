# -*- coding: utf-8 -*-

import json
import traceback
import os, sys
sys.path.append(os.getcwd().replace("spiders",""))
from spiders.BaseSpider import BaseSpider
from configuration.settings import USE_PROXY as use_proxy
from configuration.settings import CATEGORY_START_PAGE as start_page_number
from configuration.settings import CATEGORY_END_PAGE as end_page_number
from configuration.settings import BOOK_URL_QUEUE_EXCHANGE as book_url_queue_exchange
from database.RabbitMQ import RabbitmqServer
from urllib.error import URLError


class BookUrlSpider(BaseSpider):
    def __init__(self, start_url):
        # super(BookUrlSpider, self).__init__()
        self.url = start_url
        self.category_url = {}

    def parse(self):
        try:
            self._get_category_url()
            for key, value in self.category_url.items():
                self._get_book_url_from_each_category(category_url=value, category_name=key)
        except URLError as e:
            print(traceback.format_exc(), e.reason)

    def _get_category_url(self):
        try:
            selector = self.process_url_request(url=self.url, use_proxy=use_proxy)
            if selector != None:
                url_list = selector.xpath('//*[@id="leftNav"]/ul[2]/ul/div/li/span/a/@href')
                category_names = selector.xpath('//*[@id="leftNav"]/ul[2]/ul/div/li/span/a/span/text()')
                for index in range(0, len(url_list), 1):
                    url = "https://www.amazon.com" + url_list[index]
                    self.category_url[category_names[index]] = url
        except URLError as e:
            print(traceback.format_exc(), e.reason)


    def _get_book_url_from_each_category(self, category_url, category_name):
        selector = self.process_url_request(category_url,use_proxy=use_proxy)
        try:
            if selector is not None:
                print(category_url)
                # page_url = "https://www.amazon.com" + selector.xpath('//*[@id="pagn"]/span[3]/a/@href')[0]
                print(selector, type(selector))
                print(str(selector))
                url_content = selector.xpath('//span[@class="pagnLink"][1]/a/@href')
                print(url_content)
                page_url = "https://www.amazon.com" + selector.xpath('//span[@class="pagnLink"][1]/a/@href')[0]
                url_prefix = page_url.split("&page=2&")[0]
                url_suffix = page_url.split("&page=2&")[1]
                for page_index in range(start_page_number, end_page_number + 1, 1):
                    page_url = url_prefix + "&page=" + str(page_index) + "&" + url_suffix
                    selector = self.process_url_request(url=page_url, use_proxy=use_proxy)
                    if selector is not None:
                        book_url_list = selector.xpath(
                            '//*[@id="s-results-list-atf"]/li/div/div[@class="a-fixed-left-grid"]/div/div[2]/div[1]/div[1]/a/@href')
                        for book_url in book_url_list:
                            book = {}
                            book["url"] = book_url
                            book["category_name"] = category_name
                            book["try_number"] = 0
                            # print(json.dumps(book,indent=2))
                            # 将抓取的book url保存到对应的queue中。
                            # RabbitmqServer.add_message(message=json.dumps(book),
                            #                            routing_key=book_url_queue_exchange['routing_key'],
                            #                            queue=book_url_queue_exchange['queue'],
                            #                            queue_durable=book_url_queue_exchange['queue_durable'],
                            #                            exchange=book_url_queue_exchange['exchange'],
                            #                            exchange_type=book_url_queue_exchange['exchange_type'])
        except URLError as e:
            print(traceback.format_exc(), e.reason)


if __name__ == "__main__":
    start_url = "https://www.amazon.com/books-used-books-textbooks/b/ref=nav_shopall_bo_t3?ie=UTF8&node=283155"
    spider = BookUrlSpider(start_url=start_url)
    spider.parse()