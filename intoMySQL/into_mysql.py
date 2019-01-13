# -*- coding:utf-8 -*-

import json
import copy
import traceback
import os, sys
sys.path.append(os.getcwd().replace("intoMySQL",""))

from database.MysqlDatabaseClass import MySQLDatabaseClass


class IntoMySQL(object):
    def __init__(self,book_table, used_book_table):
        self.mysql = MySQLDatabaseClass()
        self.book_table = book_table
        self.used_book_table = used_book_table
        self.total_number = 0
        self.drop_number = 0

    def write_mysql(self, data_file_name):
        data_file = open(data_file_name, "r")
        for line in data_file:
            self.total_number += 1
            book = json.loads(line)
            used_book_list = copy.deepcopy(book["used_book_list"])
            book.pop("used_book_list")
            book.pop("used_book_page")
            try:
                book["number_of_used_crawled"] = len(used_book_list)
            except:
                book["number_of_used_crawled"] = 0

            try:
                if book["amazon_price"] < book["lowest_used_price"]:
                    line = json.loads(line)
                    print("#############")
                    print(json.dumps(line,indent=2))
            except Exception as e:
                print(traceback.format_exc(), e.args[0])

            # if book["ISBN_13"] is not None and book["ISBN_10"] is not None:
            #     self.mysql.insert(table=self.book_table, record=book)
            #     print "writing used books..."
            #     if used_book_list is not None and len(used_book_list) > 0:
            #         self._write_used_book(used_book_list=used_book_list, isbn_13=book["ISBN_13"],isbn_10=book["ISBN_10"])
            #         pass
            # else:
            #     self.drop_number += 1


    def _write_used_book(self, used_book_list, isbn_13, isbn_10):
        for index in range(0, len(used_book_list), 1):
            used_book = used_book_list[index]
            used_book["ISBN_index"] = isbn_10 + '-' + isbn_13 + '-' + str(index)
            used_book["ISBN_13"] = isbn_13
            used_book["ISBN_10"] = isbn_10
            self.mysql.insert(table=self.used_book_table,record=used_book)


if __name__ == "__main__":
    data_file = "./../data/book_info.json"
    book_talbe = "book_info"
    used_book_table = "used_book"
    mysql = IntoMySQL(book_table=book_talbe,used_book_table=used_book_table)
    mysql.write_mysql(data_file_name=data_file)
    mysql.mysql.close()
    print("total:", mysql.total_number)
    print("drop :", mysql.drop_number)