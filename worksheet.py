#!/usr/bin/python
# -*-coding: utf-8-*-

from datetime import datetime
from utiles import convert
import sqlite3
import parse
import DBMS
import os

parse.update_prices(update_dynamics=True,
                    replace_current=False,
                    show_process=True,
                    add_new=True)
# DBMS.validate_all(dynamics=True, show_process=True)

# DBMS.pack_data(show_process=True)
# DBMS.pack_dynamics(show_process=True)

# DBMS.unpack_dynamics(show_process=True)
# DBMS.unpack_data()


with sqlite3.connect(os.path.join(DBMS.ARCHIVE, DBMS.coins_database)) as connection:
    connection.create_function("CONVERT", 1, convert)
    cursor = connection.cursor()

    sql_data_query = """
        SELECT release_date, short_title, circulation, int_price, cat_price, existence
        FROM coins
        ORDER BY CONVERT(release_date)
    """

    sql_stats_query = """
        SELECT "Всего:", NULL, NULL, SUM(int_price) || " грн.", SUM(cat_price) || " грн.", COUNT(*) || " шт."
        FROM (%s)
    """ % sql_data_query

    sql_ex_stats_query = """
        SELECT "Имеется:", NULL, NULL, SUM(int_price) || " грн.", SUM(cat_price) || " грн.", COUNT(*) || " шт."
        FROM (%s)
        WHERE existence = '+'
    """ % sql_data_query

    coins_data = cursor.execute(sql_data_query    ).fetchall()
    all_stats  = cursor.execute(sql_stats_query   ).fetchall()
    exis_stats = cursor.execute(sql_ex_stats_query).fetchall()

    headers = ["Дата выпуска", "Краткое название", "Тираж", "Цена", "Каталог", "Наличие"]
    DBMS.print_table(data=coins_data + exis_stats + all_stats, headers=headers, tablefmt="pretty")


'''
with sqlite3.connect(os.path.join(DBMS.ARCHIVE, DBMS.prices_database)) as connection:
    connection.create_function("CONVERT", 1, convert)
    cursor = connection.cursor()
    
    # SUBSTR(day, 1, 7)
    sql_query = """
        SELECT day, SUM(price)
        FROM prices
        WHERE release_date LIKE '%2016'
        GROUP BY day
        ORDER BY 1
    """

    data = cursor.execute(sql_query).fetchall()

    headers = ["Даты", "Стоимость"]
    DBMS.print_table(data=data, headers=headers, tablefmt="pretty")
'''
# python C:\\Users\\HP_650\\Desktop\\НБУ\\SQL_worksheet.py
