#!/usr/bin/python
# -*-coding: utf-8-*-

from datetime import date, datetime
import DBMS
import re


def convert(date_field: str) -> str:
	''' Преобразование даты к нужному формату '''
	return datetime.strptime(date_field, DBMS.date_format).strftime(DBMS.sql_date_format)


def title_formating(title: str) -> str:
	''' Форматирование заглавия монеты '''
	title = title.replace('\"', '\'').split(' ')
	title[0] = title[0].capitalize()
	title = ' '.join(title)
	return title


def valid_date(data) -> bool:
	''' Валидация даты '''  
	try:
		data = datetime.strptime(data, "%d.%m.%Y")
		return datetime.strptime("01.01.1995", "%d.%m.%Y") < data <= datetime.now()
	except:
		return False


def valid_int(data) -> bool:
	''' Валидация целого положительного '''
	try:
		num = int(data)
		return num >= 0
	except:
		return False


def valid_float(data) -> bool:
	''' Валидация вещественного положительного '''
	try:
		num = float(data)
		return num > 0
	except:
		return False
