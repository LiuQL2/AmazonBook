# -*- coding: utf-8 -*-

import math
import json
import traceback
import os, sys
sys.path.append(os.getcwd().replace("spiders",""))
from spiders import BaseSpider
from configuration.settings import USE_PROXY as use_proxy


class UsedBookSpider(BaseSpider):
    def __init__(self, url, used_book_number):
        self.url = url
        self.used_page_urls = []
        self.used_books = []
        self.used_page_urls.append(self.url)
        self.used_book_number = used_book_number
        self.used_page_number = int(math.ceil(float(used_book_number)/10))

    def parse(self):
        """
        获得每一个页面里面的所有二手书信息
        :return: Nothing to return.
        """
        self._get_page_url()
        for url in self.used_page_urls:
            print "used page_url", url
            selector = self.process_url_request(url=url,use_proxy=use_proxy)
            if selector != None:
                book_selector_list = selector.xpath('//*[@id="olpOfferList"]/div/div/div[@class="a-row a-spacing-mini olpOffer"]')
                for book_selector in book_selector_list:
                    book = self._parse_one_book(selector=book_selector)
                    if book is not None:self.used_books.append(book)

    def _parse_one_book(self, selector):
        """
        提取每一本二手书的信息
        :param selector: 包含二手书信息的xpath数据块
        :return: dict，包含该本书的各个字段。
        """
        try:
            book = {}
            used_price = selector.xpath('div[1]/span/text()')[0].replace("$", "").replace("\n", "").replace(" ", "")
            book["used_price"] = float(used_price)


            ship_price_content = selector.xpath('div[1]/p/span/span[1]/text()')
            if len(ship_price_content) > 0:
                ship_price = ship_price_content[0].replace("$", "").replace("\n", "").replace(" ", "")
                book["ship_price"] = float(ship_price)
            else:
                book["ship_price"] = 0.0

            used_condition = selector.xpath('div[2]/div/span/text()')[0].split("-")[-1].replace("\n", "").replace(" ",
                                                                                                                  "")
            book["used_condition"] = used_condition

            seller_star = selector.xpath('div[4]/p/i/span/text()')[0].split(" out")[0]
            book["seller_star"] = float(seller_star)

            positive_percentage = selector.xpath('div[4]/p/a/b/text()')[0].split("%")[0]
            book["positive_percentage"] = float(positive_percentage) / 100.0

            seller_rating_number = selector.xpath('div[4]/p/text()[3]')[0].split("(")[-1].split(" ")[0].replace(",", "")
            book["seller_rating_number"] = int(seller_rating_number)

            seller_url = selector.xpath('div[4]/h3/span/a/@href')[0]
            book["seller_url"] = "https://www.amazon.com" + seller_url
            return book

        except Exception, e:
            print traceback.format_exc(), e.message
            return None

    def _get_page_url(self):
        if self.used_book_number > 10:
            selector = self.process_url_request(url=self.url, use_proxy=use_proxy)
            if selector is not None:
                page_2_url = "https://www.amazon.com" + selector.xpath('//*[@id="olpOfferListColumn"]/div[2]/ul/li[3]/a/@href')[0]
                url_prefix = page_2_url.split("_page_2")[0]
                url_suffix = page_2_url.split("_page_2")[-1].replace("startIndex=10","")

                for index in range(2, self.used_page_number + 1, 1):
                    url = url_prefix + "_page_" + str(index) + url_suffix + "startIndex=" + str((index-1)*10)
                    self.used_page_urls.append(url)


if __name__ == "__main__":
    pass