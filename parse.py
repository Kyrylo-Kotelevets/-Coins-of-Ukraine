#!/usr/bin/python
# -*-coding: utf-8-*-

from PIL import Image, ImageDraw
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import utiles
import shutil
import DBMS
import re
import os

source = 'https://www.ua-coins.info'
not_precious = source + '/catalog/base/all'
header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',}


def make_double_image(year: str, title: str, im_size: int=200) -> None:
	''' Нормализация и склеивание аверса и реверса '''
	way = os.path.join(DBMS.DIRECTORY, year, title, "Фото")
	
	''' Открытие изображений аверса и реверса '''
	avers  = Image.open(os.path.join(way, "Аверс"  + ".jpg")).resize((im_size, im_size), Image.ANTIALIAS)
	revers = Image.open(os.path.join(way, "Реверс" + ".jpg")).resize((im_size, im_size), Image.ANTIALIAS)

	''' Новое изображение из аверса и реверса '''
	image = Image.new('RGB', (2 * im_size, im_size), "grey")
	image.paste(avers,  (      0, 0))
	image.paste(revers, (im_size, 0))

	''' Сохранение комлекта фото '''
	image.save( os.path.join(way, "Изображение" + ".jpg"), size=(2 * im_size, im_size))
	avers.save( os.path.join(way, "Аверс"       + ".jpg"), size=(    im_size, im_size))
	revers.save(os.path.join(way, "Реверс"      + ".jpg"), size=(    im_size, im_size))


def parse_dynamics(coin, year: str, title: str, show_process: bool=False) -> None:
	''' Парсинг динамики цен '''
	url = source + coin.a.get('href')
	req = requests.get(url, headers=header)

	if req:
		''' Преобразование страницы с монетой в xml '''
		page = BeautifulSoup(req.text, 'lxml')
		path = os.path.join(DBMS.DIRECTORY, year, title, "Динамика")
		
		''' Если еще нет нужной папки '''
		if not os.path.exists(path):
			os.mkdir(path)

		''' Перебираем все скрипты на странице '''
		for script in page.findAll('script'):
			''' Ищем данные вида: [new Date(2016, 6, 19), 76] '''
			date_regex = r'\[new Date\([1, 2][0, 1, 2, 9][0-9]{2}, [0-9]{1,2}, [0-9]{1,2}\), [0-9]*\]'
			result = re.findall(date_regex, str(script))

			''' Если попался скрипт с датами '''
			if result:
				if show_process:
					print("Загрузка динамики")

				''' Переформатируем данные '''
				for date in sorted(result, reverse=True):
					''' Оставлям только числа и запятые-разделители '''
					items = re.sub(r'[^0-9, \,]', '', date)
					''' Разбиваем на лексемы и приводим к числам'''
					year, month, day, price = map(int, items.split(', '))
					month += 1
					
					date = datetime(year=year, month=month, day=day).strftime(DBMS.sql_date_format)
					temp_path = os.path.join(path, date + ".txt")
					
					''' Если дошли до последней существующей даты '''
					if os.path.exists(temp_path):
						return

					''' Проверяем цену на корректность '''
					try:
						int(price)
					except:
						continue
					else:
						''' Если все хорошо, записываем в соответсвующий файл '''
						with open(temp_path, 'wt', encoding=DBMS.code) as file:
							file.write(str(price))

					''' Опционально выводим внесенные данные '''
					if show_process:
						print('\t', date, price)
	else:
		raise Exception("Сбой при попытке загрузки страницы")


# TODO os.makedirs
# TODO повышение стабильности dict['default']
def add_coin(coin, year: str, title: str, show_process: bool=False) -> None:
	''' Парсинг монеты и данных о ней '''

	temp_path = os.path.join(DBMS.DIRECTORY, year)

	''' Если это первая монета из года '''
	if not os.path.exists(temp_path):
		os.mkdir(temp_path)

	''' Цена монеты '''
	price = re.sub(r'\D', '', coin.find('td', {'data-title': f'Цена {DBMS.today}'}).text)

	temp_path = os.path.join(temp_path, title)

	''' Если этой монеты ещё нет в базе данных '''
	if not os.path.exists(temp_path):
		url = source + coin.a.get('href')
		req = requests.get(url, headers=header)

		if req:
			if show_process:
				print("Загрузка данных монеты")

			''' Преобразование страницы с монетой в xml '''
			page = BeautifulSoup(req.text, 'lxml')

			# ['Дата выпуска', 'Номинал', 'Материал', 'Вес', 'Диаметр', 'Тираж', 'Серия', 'Цена']
			info = list(map(lambda x: x.text, page.find('table', {'class': 'coin-info'}).findAll('tr')[1].findAll('td'))) + [page.find('div', {'class': 'category'}).a.text, price]
			info[5] = ''.join(filter(lambda x: x.isdigit(), info[5]))

			if show_process:
				print('\t', info)

			try:
				int(info[7])
			except:
				info[7] = '0'

			# Поиск ссылок на аверс и реверс
			avers, revers = None, None
			for img in page.findAll('img'):
				if img.get('alt'):
					if avers is  None and 'Аверс'  in img['alt']:
						avers = source + img['src']
					if revers is None and 'Реверс' in img['alt']:
						revers = source + img['src']

			''' Опционально выводим ссылки '''
			if show_process:
				print('\t', [avers, revers])

			''' Создание папки для монеты '''
			os.mkdir(temp_path)

			''' Запись данных по соответствующим файлам '''
			for name, data in zip(['Дата выпуска', 'Номинал', 'Материал', 'Вес', 'Диаметр', 'Тираж', 'Серия', 'Цена', 'Название', 'Краткое название', 'Наличие', 'Сохранность', 'Примечания', 'Каталог'], info + [title, title, '-', '', '', info[7]]):
				open(os.path.join(temp_path, name + '.txt'), 'w', encoding=DBMS.code).write(data)

			temp_path = os.path.join(temp_path, "Фото")
			''' Папка для хранения изображений монеты '''
			os.mkdir(temp_path)

			''' Загрузка фото аверса и реверса '''
			open(os.path.join(temp_path, "Аверс"  + ".jpg"), 'wb').write(requests.get(avers,  headers=header).content)
			open(os.path.join(temp_path, "Реверс" + ".jpg"), 'wb').write(requests.get(revers, headers=header).content)

			''' Сдвоивание изображений '''
			make_double_image(year, title)
		else:
			raise Exception("Сбой при попытке загрузки страницы")


def update_prices(update_dynamics: bool=False,
				  show_process:    bool=True,
				  replace_current: bool=False,
				  add_new:         bool=True) -> None:
	''' Обновление цен всех монет из базы данных '''

	''' Если сегодня обновляли '''
	if not replace_current and os.path.exists(os.path.join(DBMS.ARCHIVE, DBMS.coins_database)):
		print("Цены на момент %s уже обновлены" % DBMS.today)
		return

	''' Если папка отсутсвует, создаём '''
	if not os.path.exists(DBMS.DIRECTORY):
		os.mkdir(DBMS.DIRECTORY)

	''' Запрос страницы со списком недрагоценных монет '''
	req = requests.get(not_precious, headers=header)
	
	''' При удачном запросе '''
	if req:
		soup = BeautifulSoup(req.text, 'lxml')
		
		''' Обновляем цену каждой монеты из списка '''
		for coin in soup.table.find_all(['tr'])[1:-1]:
			if len(coin.find_all(['td'])) == 5 and coin.a.text:
				''' Парсим название и год выпуска монеты '''
				title = utiles.title_formating(coin.a.text)
				year = coin.td.text[-4:]
				path = os.path.join(DBMS.DIRECTORY, year, title)

				print(f"{year} - «{title}»")

				''' Если этой монеты пока нет в базе данных '''
				if not os.path.exists(path):
					''' Если необходимо, добавляем '''
					if add_new:
						''' Добавляем данные о монете'''
						add_coin(      coin, year, title, show_process=show_process)
						if show_process:
							print("Данные загружены")

						''' Записываем её динамику '''
						parse_dynamics(coin, year, title, show_process=show_process)
						if show_process:
							print("Динамика загружена")

						print()
				else:
					''' Парсим и чистим новую цену '''
					new_price = re.sub(r'\D', '', coin.find('td', {'data-title': f'Цена {DBMS.today}'}).text) or '0'
					
					''' Перезаписываем новую цену '''
					with open(os.path.join(path, "Цена" + ".txt"), 'wt') as file:
						file.write(str(new_price))
					if show_process:
						print("Стоимость обновлена")

					''' Если необходимо обновлять динамику '''
					if update_dynamics:
						parse_dynamics(coin, year, title, show_process=show_process)
						if show_process:
							print("Динамика дополнена")
					
					print()
		print(f'Цены на момент {DBMS.today} были обновлены')

		''' После удачного обновления создаём копию базы '''
		DBMS.pack_data()
	else:
		print("Сбой обновления цен")
