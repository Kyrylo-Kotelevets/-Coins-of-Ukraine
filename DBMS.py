#!/usr/bin/python
# -*-coding: utf-8-*-

from tabulate import tabulate
from datetime import datetime
import sqlite3
import utiles
import shutil
import os

code = "utf-8"
file_extension = ".txt"
img_extension  = ".jpg"
date_format     = "%d.%m.%Y"
sql_date_format = "%Y-%m-%d"
DIRECTORY_NAME = "DATABASE"
ARCHIVE_NAME   = "HISTORY"
ROOT = os.path.join("C:\\", "Users", "HP_650", "Desktop", "Coins of Ukraine")
DIRECTORY = os.path.join(ROOT, DIRECTORY_NAME)
ARCHIVE   = os.path.join(ROOT, ARCHIVE_NAME  )


today     = datetime.now().strftime(    date_format)
sql_today = datetime.now().strftime(sql_date_format)
coins_database  = "coins %s.db" % sql_today
prices_database = "PRICES.db"

nominals = ["2", "5", "10", "200000"]
metals = ["нейзильбер", "мельхиор", "сплав на основе цинка", "биметал (недраг.)"]

FILES = {
    "Название"         : {"ENG" : "title",        "default" :  None, "pattern" : lambda x: True},
    "Краткое название" : {"ENG" : "short_title",  "default" :  None, "pattern" : lambda x: True},
    "Дата выпуска"     : {"ENG" : "release_date", "default" : today, "pattern" : lambda x: utiles.valid_date(x)},
    "Номинал"          : {"ENG" : "nominal",      "default" :  None, "pattern" : lambda x: x in nominals},
    "Серия"            : {"ENG" : "series",       "default" :  None, "pattern" : lambda x: True},
    "Тираж"            : {"ENG" : "circulation",  "default" :  None, "pattern" : lambda x: utiles.valid_int(x)},
    "Материал"         : {"ENG" : "metal",        "default" :  None, "pattern" : lambda x: x in metals},
    "Вес"              : {"ENG" : "weight",       "default" :  None, "pattern" : lambda x: utiles.valid_float(x)},
    "Диаметр"          : {"ENG" : "diameter",     "default" :  None, "pattern" : lambda x: utiles.valid_float(x)},
    "Цена"             : {"ENG" : "int_price",    "default" :     0, "pattern" : lambda x: utiles.valid_int(x)},
    "Каталог"          : {"ENG" : "cat_price",    "default" :     0, "pattern" : lambda x: utiles.valid_int(x) or x == '0'},
    "Наличие"          : {"ENG" : "existence",    "default" :   '-', "pattern" : lambda x: x in ['-', '+']},
    "Сохранность"      : {"ENG" : "safety",       "default" :    '', "pattern" : lambda x: x == '' or utiles.valid_int(x)},
    "Примечания"       : {"ENG" : "notes",        "default" :    '', "pattern" : lambda x: True}
}


IMAGES = {
    'Аверс'       : {"ENG" : 'obverse'},
    'Реверс'      : {"ENG" : 'reverse'},
    'Изображение' : {"ENG" : 'image'}
}

ATTRS = dict(FILES, **IMAGES)

sql_create_coins_table = '''
CREATE TABLE IF NOT EXISTS coins
(
    title        TEXT    NOT NULL CONSTRAINT title_len       CHECK (LENGTH(title) <= 150),
    short_title  TEXT    NOT NULL CONSTRAINT short_title_len CHECK (LENGTH(short_title) <= LENGTH(title)),
    release_date DATE    NOT NULL CONSTRAINT actual_date     CHECK (DATE(release_date) >= DATE(\'01.01.1995\') AND DATE(release_date) <= DATE(\'now\')),
    nominal      INTEGER NOT NULL CONSTRAINT valid_nominal   CHECK (nominal IN (2, 5, 10, 200000)),
    series       TEXT    NOT NULL CONSTRAINT length_seria    CHECK (LENGTH(series) > 4 AND LENGTH(series) <= 60),
    circulation  INTEGER NOT NULL CONSTRAINT positive_circ   CHECK (circulation > 0),
    metal        TEXT    NOT NULL CONSTRAINT length_metal    CHECK (LENGTH(metal) < 50),
    weight       REAL    NOT NULL CONSTRAINT posit_weight    CHECK (weight > 0),
    diameter     REAl    NOT NULL CONSTRAINT posit_diameter  CHECK (diameter > 0),
    int_price    INTEGER NOT NULL CONSTRAINT posit_int_price CHECK (int_price >= 0),
    cat_price    INTEGER NOT NULL CONSTRAINT posit_cat_price CHECK (cat_price >= 0),
    existence    TEXT    NOT NULL CONSTRAINT valid_existence CHECK (existence = \'+\'OR existence = \'-\'),
    safety       INTEGER          CONSTRAINT valid_safety    CHECK (safety >= 60 OR safety <= 70),
    notes        TEXT             CONSTRAINT too_long_node   CHECK (LENGTH(notes) <= 200),

    obverse BLOB NOT NULL,
    reverse BLOB NOT NULL,
    image   BLOB NOT NULL,

    PRIMARY KEY  (release_date, title, metal)    
)
'''

sql_create_prices_table = '''
CREATE TABLE IF NOT EXISTS prices
(
    day   DATE    NOT NULL CONSTRAINT actual_date CHECK (DATE(day) >= DATE(\'01.01.1995\') AND DATE(day) <= DATE(\'now\')),
    price INTEGER NOT NULL CONSTRAINT posit_price CHECK (price >= 0),
    
    release_date  DATE    NOT NULL CONSTRAINT actual_rdate  CHECK (DATE(release_date) >= DATE(\'01.01.1995\') AND DATE(release_date) <= DATE(\'now\')),
    title         TEXT    NOT NULL CONSTRAINT title_len     CHECK (LENGTH(title) <= 150),
    metal         TEXT    NOT NULL CONSTRAINT length_metal  CHECK (LENGTH(metal) < 50),

    PRIMARY KEY (release_date, title, metal, day)
)
'''

sql_coins_insert = "INSERT INTO coins VALUES (%s)" % ', '.join('?' * len(ATTRS))

sql_prices_insert = "INSERT OR REPLACE INTO prices VALUES (?, ?, ?, ?, ?)"

sql_select_all = "SELECT %s FROM coins" % ', '.join(item["ENG"] for item in ATTRS.values())


def validate_all(dynamics: bool=False,
                 show_process: bool=False) -> bool:
    ''' Проверка корректности данных в каталоге '''
    result = True
    for year in os.listdir(DIRECTORY):
        if show_process:
            print(year)
        for coin in os.listdir(os.path.join(DIRECTORY, year)):
            ''' Путь к монете '''
            way_to_coin = os.path.join(DIRECTORY, year, coin)

            if show_process:
                print('\t', coin)

            for filename in FILES.keys():
                way_to_file = os.path.join(way_to_coin, filename + file_extension) 

                ''' Проверка существования файла '''
                if not os.path.exists(way_to_file):
                    result = False
                    print(f'({year}) > {coin}: отсутствует файл {filename}')
                else:
                    data = open(way_to_file, 'rt', encoding=code).read()
                    ''' Проверка корректности содержимого файла '''
                    if not FILES[filename]["pattern"](data):
                        result = False
                        print(f'({year}) > {coin} > {filename}: некорректное содержимое: {data}')

            ''' Путь к папке с изображениями '''
            way_to_photo = os.path.join(way_to_coin, "Фото")

            if not os.path.exists(way_to_photo):
                result = False
                print(f'({year}) > {coin}: отсутствует папка с изображениями')
            else:
                ''' Проверка налчия фото '''
                for title in IMAGES.keys():
                    if not os.path.exists(os.path.join(way_to_photo, title + img_extension)):
                        result = False
                        print(f'({year}) > {coin}: отсутствует: {title}')

            ''' Путь к папке с изображениями '''
            way_to_prices = os.path.join(way_to_coin, "Динамика")

            if not dynamics:
                pass
            elif not os.path.exists(way_to_prices):
                result = False
                print(f'({year}) > {coin}: отсутствует папка с динамикой')
            else:
                ''' Проверка налчия фото '''
                for file in os.listdir(way_to_prices):
                    date = file[:-len(file_extension)]
                    price = open(os.path.join(way_to_prices, file), encoding=code).read()
                    
                    try:
                        datetime.strptime(date, sql_date_format)
                    except:
                        result = False
                        print(f'({year}) > {coin}: некорректный формат даты: {date}')

                    try:
                        int(price)
                    except:
                        result = False
                        print(f'({year}) > {coin}: некорректная стоимость: {price}')
    return result


def read(directory: str=ARCHIVE, database: str=coins_database) -> list:
    ''' Считывание данных '''
    if os.path.exists(os.path.join(directory, database)):
        ''' Открываем базу данных '''
        with sqlite3.connect(database) as connection:
            cursor = connection.cursor()
            data = cursor.execute(sql_select_all).fetchall()

            ''' Возвращаем массив словарей с данными о монетах '''
            return list({key : value for key, value in zip(FILES.keys(), coin)} for coin in data)
    else:
        raise Exception("Отсутсвует файл базы данных: %s" % database)


def print_table(data: list,
                headers: list=list(FILES.keys()),
                tablefmt: str="grid",
                align: str="center") -> None:

    ''' Табличное отображение данных '''
    if isinstance(data[0], dict):
        print(tabulate([[ind + 1] + [coin[key] for key in headers] for ind, coin in enumerate(data)],
              headers=[''] + headers,
              tablefmt=tablefmt,
              stralign=align))
    else:
        print(tabulate([[ind + 1] + list(coin) for ind, coin in enumerate(data)],
              headers=[''] + headers,
              tablefmt=tablefmt,
              stralign=align))


def pack_data(directory: str=ARCHIVE,
              show_process: bool=True) -> None:
 
    ''' Создание реляционной копии базы данных '''
    database = os.path.join(directory, coins_database)

    ''' Создаём при отсутствии директорию '''
    if not os.path.exists(directory):
        os.mkdir(directory)

    ''' Удаляем копию, если существует '''
    if os.path.exists(database):
        os.remove(database)
    
    ''' Создаём для монет базу и таблицу '''
    with sqlite3.connect(database) as connection:
        cursor = connection.cursor()
        cursor.execute(sql_create_coins_table)

        ''' Вставляем данные каждой монеты в таблицу '''
        for YEAR in os.listdir(DIRECTORY):
            if show_process:
                print(YEAR)
            for COIN in os.listdir(os.path.join(DIRECTORY, YEAR)):
                ''' Путь к файлам монеты '''
                files_path, images_path = os.path.join(DIRECTORY, YEAR, COIN), os.path.join(DIRECTORY, YEAR, COIN, "Фото")
                files  = list(open(os.path.join(files_path,  filename + file_extension), 'rt', encoding=code).read() for filename in FILES.keys())
                images = list(open(os.path.join(images_path, title    + img_extension ), 'rb'               ).read() for title    in IMAGES.keys())

                ''' Вносим все собранное в таблицу '''
                cursor.execute(sql_coins_insert, files + images)
                
                ''' Опционально оповещаем об удачном добавлении монеты'''
                if show_process:
                    print("\tВнесена в базу:", COIN)

        ''' Подтверждаем транзакцию '''
        connection.commit()

    if show_process:
        print("База: %s успешно создана и заполнена\n" % coins_database)


def pack_dynamics(directory: str=ARCHIVE,
                  show_process: bool=True) -> None:
    
    ''' Создание реляционной копии базы данных '''
    database = os.path.join(directory, prices_database)

    ''' Создаём при отсутствии директорию '''
    if not os.path.exists(directory):
        os.mkdir(directory)

    ''' Создаём для цен базу и таблицу '''
    with sqlite3.connect(database) as connection:
        cursor = connection.cursor()
        cursor.execute(sql_create_prices_table)

        ''' Вставляем данные каждой монеты в таблицу '''
        for YEAR in os.listdir(DIRECTORY):
            print(YEAR)
            for COIN in os.listdir(os.path.join(DIRECTORY, YEAR)):
                ''' Путь к файлам монеты '''
                path = os.path.join(DIRECTORY, YEAR, COIN)
                title, release_date, metal = [open(os.path.join(path,  filename + file_extension), 'rt', encoding=code).read() for filename in ["Название", "Дата выпуска", "Материал"]]

                ''' Вносим каждую дату:цену для монеты '''
                for day, price in zip(*get_dynamics(YEAR, COIN)):
                    cursor.execute(sql_prices_insert, (day, price, release_date, title, metal))

                if show_process:
                    print("\tУпакована динамика для:", COIN)

        ''' Подтверждаем транзакцию '''
        connection.commit()

    if show_process:
        print("Динамика успешно создана и заполнена", '\n')


def unpack_data(directory: str=ROOT,
                database: str=coins_database,
                cat_name: str="Каталог",
                files:  list=FILES.keys(), 
                images: list=IMAGES.keys(),
                consume_files: list=list(),
                clean_prev: bool=True,
                show_process: bool=False) -> None:

    ''' Распаковка реляционной копии базы данных в иерархический каталог'''
    database = os.path.join(ARCHIVE, database)

    ''' Если я себя обманул и указал неверную копию '''
    if not os.path.exists(database):
        raise Exception("Отсутсвует указанная копия базы данных: %s" % database)

    with sqlite3.connect(database) as connection:
        cursor = connection.cursor()

        ''' Путь к каталогу '''
        path = os.path.join(directory, cat_name)

        ''' Для каждой монеты собираем файловые данные в нужном порядке '''
        for coin in cursor.execute(sql_select_all).fetchall():
            COIN = {key : value for key, value in zip(ATTRS.keys(), coin)}

            ''' Временный путь к монете '''
            temp_path = os.path.join(path, COIN["Дата выпуска"][-4:], COIN["Название"])

            ''' Проверяем нужно ли создавать директории '''
            if not os.path.exists(temp_path):
                os.makedirs(temp_path, exist_ok=True)
            else:
                ''' Опционально предварительно чистим папку монеты '''
                if clean_prev:
                    shutil.rmtree(temp_path)
                    os.makedirs(temp_path, exist_ok=True)

            ''' Создаём/+заполняем нужные файлы '''
            for filename in files or []:
                with open(os.path.join(temp_path, filename + file_extension), 'wt', encoding=code) as file:
                    file.write(str(COIN[filename]))

            ''' Если необходим итоговый файл '''
            if consume_files:
                with open(os.path.join(temp_path, "ДАННЫЕ.txt"), 'wt') as file:
                    file.write(tabulate([list(filename, COIN[filename]) for filename in consume_files],
                                        tablefmt="grid",
                                        stralign="center"))

            ''' Если отсутствует папка для фото, то создаём '''
            temp_path = os.path.join(temp_path, "Фото")
            if images and not os.path.exists(temp_path):
                os.mkdir(temp_path)

            ''' Сохраняем фото '''
            for imagename in images or []:
                with open(os.path.join(temp_path, imagename + img_extension), 'wb') as image:
                    image.write(COIN[imagename])

            if show_process:
                print("Внесено в каталог:", COIN["Дата выпуска"][-4:], '-', COIN["Краткое название"])

    if show_process:
        print("Директория: %s успешно создана и заполнена" % path, '\n')


def unpack_dynamics(directory: str=ROOT,
                    cat_name: str="Каталог",
                    show_process: bool=False) -> None:

    ''' Распаковка реляционной копии динамики в иерархический каталог '''
    connection = sqlite3.connect(os.path.join(ARCHIVE, prices_database))
    cursor = connection.cursor()

    ''' Если нет папки каталога, создаём '''
    directory = os.path.join(directory, cat_name)
    if not os.path.exists(directory):
        os.mkdir(directory)

    ''' Переписываем всю динамику '''
    for (COIN, YEAR, date, price) in cursor.execute("""
            SELECT title, SUBSTR(release_date, 7, 11), day, price
            FROM prices
            ORDER BY 2, 1, 3
            """).fetchall():

        temp_path = os.path.join(directory, YEAR, COIN, "Динамика")
        os.makedirs(temp_path, exist_ok=True)
        temp_path = os.path.join(temp_path, date + file_extension)
        
        ''' Создаём/перезаписываем цену в соответсвующий файл '''
        with open(temp_path, 'wt', encoding=code) as file:
            file.write(str(price))

        if show_process:
            print(YEAR, COIN, date)

    if show_process:
        print("Динамика распакована по адресу: %s" % directory, '\n')


def get_dynamics(year: str, title: str,
                 min_date: datetime=None,
                 max_date: datetime=None) -> tuple:

    ''' Получение данных о изменении стоимости '''
    temp_path = os.path.join(DIRECTORY, year, title, "Динамика")
    prices, dates = [], []

    ''' Выбираем файлы с датами в нужном диапазоне'''
    for date in os.listdir(temp_path):
        ''' Проверяем дату на попадение в диапазон '''
        if (min_date or "1995-01-01") < date < (max_date or sql_today):
            with open(os.path.join(temp_path, date), 'rt', encoding=code) as file:
                prices.append(int(file.read()))
                dates.append(date[:-4])

    return (dates, prices)
