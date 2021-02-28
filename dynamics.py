#!/usr/bin/python
# -*-coding: utf-8-*-

from sklearn.metrics import r2_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from matplotlib.ticker import AutoMinorLocator
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import sqlite3
import DBMS
import os

 
def smooth(prices: list, dates: list, k: int=7, method=lambda arr: sum(arr) / len(arr)) -> tuple:
	sm_prices, sm_dates = list(), list()
	for i in range(k, len(prices), k):
		sm_prices.append(method(prices[i - k:i]))
		sm_dates.append(dates[i - k])
	return sm_dates, sm_prices


def get_ticks(dates: list, years=True, months=False, days=False) -> tuple:
	rus_month = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
	dates = list(map(lambda d: d.split('-'), dates))
	curr_year,curr_month, curr_day = dates[0]
	ticks, labels = [], []

	for i, (year, month, day) in enumerate(dates):
		if years and curr_year != year:
			curr_year = year
			ticks.append(i)
			labels.append(curr_year)
		elif months and curr_month != month and (not years or int(month) != 1):
			curr_month = month
			ticks.append(i)
			labels.append(rus_month[int(curr_month) - 1][:3] + '.')
		elif days and curr_day != day and (not months or int(day) != 1):
			curr_day = day
			ticks.append(i)
			labels.append(str(int(curr_day)))

	return ticks, labels


coin_title = "_"
dates, price = DBMS.get_dynamics("2021", coin_title, min_date="2017-06-01")
'''
dates, price = [], []
with sqlite3.connect(os.path.join(DBMS.ARCHIVE, DBMS.prices_database)) as connection:
    cursor = connection.cursor()
    
    # SUBSTR(day, 1, 7)
    sql_query = """
        SELECT day, SUM(price)
        FROM prices
        WHERE release_date LIKE '%2007' and day > '2009-01-01'
        GROUP BY day
        ORDER BY 1
    """

    data = cursor.execute(sql_query).fetchall()

    for (day, pr) in data:
    	print(day)
    	dates.append(day)
    	price.append(pr)
'''
# dates, price = smooth(dates=dates, prices=price, k=1, method=lambda arr: max(arr))
fig, ax = plt.subplots(2, 1, gridspec_kw={"hspace" : 0.2,
										  "top"    : 0.92,
										  "bottom" : 0.05,
										  "left"   : 0.07,
										  "right"  : 0.95})

fig.patch.set_facecolor("#e7e7e7")
fig.suptitle(coin_title, fontsize=14)

X = np.arange(len(price)).reshape(-1, 1)
Y = np.array(      price).reshape(-1, 1)

poly_features = PolynomialFeatures(degree=5)
X_poly = poly_features.fit_transform(X)

reg = LinearRegression()
reg.fit(X_poly, Y)
Y_pred = reg.predict(X_poly)

print(reg.coef_)
print('Coefficient of determination: %.3f'
	  % r2_score(Y, Y_pred))
			
ax[0].plot(X, Y,      linewidth=1, color="#008ae6")
ax[1].plot(X, Y,      linewidth=1, color="#008ae6")
ax[0].plot(X, Y_pred, linewidth=1, color="#e60000")
ax[1].fill([0, *X, X.max()], [0, *Y, 0], color="#80ccff")


for i in range(2):
	ax[i].set_ylabel('Стоимость (грн.)')

	ax[i].set(xlim=(0, X.max()), ylim=(0, Y.max() * 1.25))
	ticks, labels = get_ticks(dates) 

	ax[i].set_xticks(ticks=ticks, minor=False)
	ax[i].set_xticklabels(labels=labels)
	ax[i].tick_params(axis='x', which='major', labelsize = 10)
	ax[i].yaxis.set_minor_locator(AutoMinorLocator())

	ax[i].grid(axis='y',    which='minor', color='#c7c7c7', linewidth=0.4)
	ax[i].grid(axis='both', which='major', color='#a2a2a2', linewidth=0.75)


fig.set_figwidth(13)
fig.set_figheight(6)
plt.show()
