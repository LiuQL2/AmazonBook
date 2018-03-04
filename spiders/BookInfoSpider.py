# -*- coding:utf-8 -*-

import re
import json
import datetime
import traceback
import os, sys
sys.path.append(os.getcwd().replace("spiders",""))

from configuration.settings import BOOK_INFO_QUEUE_EXCHANGE as book_info_queue_exchange
from configuration.settings import BOOK_URL_QUEUE_EXCHANGE as book_url_queue_exchange
from configuration.settings import URL_TRY_NUMBER as url_try_number
from database.RabbitMQ import RabbitmqServer
from spiders import BaseSpider
from spiders.UsedBookInfo import UsedBookSpider


class BookInfoSpider(BaseSpider):
    def __init__(self, url_count, use_proxy):
        self.url = url_count["url"]
        self.url_count = url_count
        self.url_count["try_number"] += 1
        self.use_proxy = use_proxy
        self.book = {}
        self.book["url"] = self.url
        self.book["category_name"] = url_count["category_name"]

    def parse(self):
        mode = re.compile(r'\d+')

        try:
            self.selector = self.process_url_request(url=self.url, use_proxy=self.use_proxy)

            book_type = self.selector.xpath('//*[@id="title"]/span[2]/text()')[0]

            try:
                book_title = self.selector.xpath('//*[@id="productTitle"]/text()')[0]
                self.book["title"] = book_title
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["title"] = None

            try:
                amazon_price = self.selector.xpath('//*[@id="tmmSwatches"]/ul/li[1]/span/span[1]/span/a/span[2]/span/text()')[0].replace("$", "").replace("\n", "").replace(" ", "")
                self.book["amazon_price"] = float(amazon_price)
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["amazon_price"] = None

            try:
                list_price = self.selector.xpath('//*[@id="buyBoxInner"]/div[1]/div[2]/ul/li[1]/span/span[2]/text()')[0].replace("$", "").replace("\n", "").replace(" ", "")
                self.book["list_price"] = float(list_price)
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["list_price"] = self.book["amazon_price"]

            try:
                review_number = self.selector.xpath('//*[@id="reviewSummary"]/div[1]/a/div/div/div[2]/div/span/text()')[
                    0].replace("\n", "").replace(" ", "").replace(",", "")
                self.book["review_number"] = int(review_number)

                review_star = self.selector.xpath('//*[@id="reviewSummary"]/div[2]/span/a/span/text()')[0].split(" ")[0]
                self.book["review_star"] = float(review_star)
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["review_number"] = None
                self.book["review_star"] = None

            try:
                used_book_page = self.selector.xpath('//*[@id="tmmSwatches"]/ul/li[1]/span/span[3]/span[1]/a/@href')[0]
                self.book["used_book_page"] = "https://www.amazon.com" + used_book_page
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["used_book_page"] = None


            try:
                sale_rank = self.selector.xpath('//li[@id="SalesRank"]/text()[2]')[0].replace("#", "").replace("\n","").replace(" ", "").replace(",", "")
                self.book["sale_rank"] = int(mode.findall(sale_rank)[0])
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["sale_rank"] = None

            product_details = self.selector.xpath('//*[@id="productDetailsTable"]//div/ul/li')

            for temp_selector in product_details:
                name_id = temp_selector.xpath('b/text()')[0].split(":")[0]
                text = temp_selector.xpath('text()')

                if name_id == "ISBN-10":
                    isbn_10 = text[0].replace("\n","").replace(" ", "")
                    self.book["ISBN_10"] = isbn_10
                elif name_id == "ISBN-13":
                    ISBN_13 = text[0].replace("\n","").replace(" ", "")
                    self.book["ISBN_13"] = ISBN_13
                elif name_id == "Publisher":
                    publisher_content = text[0]
                    publisher = publisher_content.split(";")[0]
                    self.book["publisher"] = publisher
                    publish_date = publisher_content.split("(")[-1].replace(")", '')
                    publish_date = datetime.datetime.strptime(publish_date, '%B %d, %Y')
                    self.book["publish_date"] = publish_date.strftime("%Y-%m-%d")

                    now_time = datetime.datetime.now()
                    self.book["publish_days"] = (now_time - publish_date).days
                else:
                    pass

            self.book.setdefault("ISBN_10",None)
            self.book.setdefault("ISBN_13",None)
            self.book.setdefault("publisher",None)
            self.book.setdefault("publish_date",None)
            self.book.setdefault("publish_days",None)

            format_list = self.selector.xpath('//*[@id="tmmSwatches"]/ul/li')
            for format in format_list:
                format_type = format.xpath('span/span[1]/span[1]/a/span[1]/text()')[0]

                if str(format_type).replace(" ","").lower() == str(book_type).replace(" ","").lower():
                    print format_type, book_type
                    try:
                        lowest_used_price = format.xpath('span/span[3]/span[1]/a/text()[2]')[0].replace("$", "").replace("\n", "").replace(" ", "")
                        self.book["lowest_used_price"] = float(lowest_used_price)
                        number_of_used = format.xpath('span/span[3]/span[1]/a/text()[1]')[0].replace("\n", "").replace(" ", "")
                        self.book["number_of_used"] = int(mode.findall(number_of_used)[0])
                        used_page_url = "https://www.amazon.com/" + format.xpath('span/span[3]/span[1]/a/@href')[0]
                        self.book["used_page_url"] = used_page_url
                        amazon_price = format.xpath('span/span[1]/span[1]/a/span[2]/span/text()')[0].replace("$", "").replace("\n", "").replace(" ", "")
                        self.book["amazon_price"] = float(amazon_price)


                    except Exception, e:
                        print traceback.format_exc(), e.message
                        self.book["lowest_used_price"] = None
                        self.book["number_of_used"] = None
                        self.book["used_page_url"] = None
                    break
                else:
                    pass

            try:
                used_book_spider = UsedBookSpider(url=self.book["used_page_url"],used_book_number=self.book["number_of_used"])
                used_book_spider.parse()
                self.book["used_book_list"] = used_book_spider.used_books
            except Exception, e:
                print traceback.format_exc(), e.message
                self.book["used_book_list"] = None

            print(json.dumps(self.book,indent=2))
            RabbitmqServer.add_message(message=json.dumps(self.book),
                                       routing_key=book_info_queue_exchange['routing_key'],
                                       queue=book_info_queue_exchange['queue'],
                                       queue_durable=book_info_queue_exchange['queue_durable'],
                                       exchange=book_info_queue_exchange['exchange'],
                                       exchange_type=book_info_queue_exchange['exchange_type'])

        except Exception, e:
            print traceback.format_exc(), e.message
            if self.url_count["try_number"] < url_try_number:
                RabbitmqServer.add_message(message=json.dumps(self.url_count),
                                       routing_key=book_url_queue_exchange['routing_key'],
                                       queue=book_url_queue_exchange['queue'],
                                       queue_durable=book_url_queue_exchange['queue_durable'],
                                       exchange=book_url_queue_exchange['exchange'],
                                       exchange_type=book_url_queue_exchange['exchange_type'])


if __name__ == "__main__":
    url = {
        "url":"https://www.amazon.com/Wreck-This-Journal-Duct-Expanded/dp/0399162704/ref=sr_1_97/143-2414466-1723212?s=books&ie=UTF8&qid=1513778577&sr=1-97",
        "category_name":"qewwe",
        "try_number":0
    }

    # url = {
    #     "url":"https://www.amazon.com/Origami-Dover-Papercraft-simple-projects/dp/0486272982/ref=tmm_pap_swatch_0?_encoding=UTF8&qid=1513778564&sr=1-27",
    #     "category_name":"qewwe",
    #     "try_number":0
    # }
    book = BookInfoSpider(url,use_proxy=True)
    book.parse()