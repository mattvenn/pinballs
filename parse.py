#!/usr/bin/python

""""
looks up historical sell prices from pinpedia.com
"""

import arrow
import sys
import numpy as np
import csv
import time
import glob

from datetime import datetime
from currencies import currencies
from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import re

html_dir = 'html'
csv_dir = 'csv'

def parse_page(html):
    soup = BeautifulSoup(html)
    headers = soup.findAll("h4")

    #import ipdb; ipdb.set_trace()
    machines = []
    for header in headers:
        aref = header.findChildren()[1]
        url = aref.attrs[0][1]
        machine = url.replace('http://www.pinpedia.com/machine/','')
        machines.append(machine)
    return machines

def get_machines(start,num_pages):
    mech = Browser()
    mech.set_handle_robots(False)
    mech.set_handle_equiv(False) 
    mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    machines = []
    try:
        page_num = 0
        for page_num in range(start,num_pages+1):
            print("page %d" % (page_num))
            url = "http://www.pinpedia.com/machine?page=%d" % page_num
            html_page = mech.open(url)
            html = html_page.read()
            machines += parse_page(html)
            time.sleep(0.1)
    except Exception as e:
        print e
        print("finished at page %s" % page_num)
    with open('machines.txt','w') as fh:
        for machine in machines:
            fh.write(machine + "\n")
    return machines

def parse(name):
    files = glob.glob("%s/%s-*html" % (html_dir,name))
    parsed_rows = []
    for file in files:
        with open(file) as fh:
            print("parsing %s" % file)
            html = fh.read()

#fetchs all available pages and saves them as html files
def fetch(name):
    mech = Browser()
    mech.set_handle_robots(False)
    mech.set_handle_equiv(False) 
    mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    try:
        page_num = 0
        for page_num in range(100):
            print("page %d for %s" % (page_num,name))
            url = "http://www.pinpedia.com/machine/%s/prices?page=%d" % (name,page_num)
            html_page = mech.open(url)
            html = html_page.read()
            with open('%s/%s-%s.html' % (html_dir,name,page_num),'w') as fh:
                fh.write(html)
            time.sleep(0.5)
    except Exception:
        print("finished at page %s" % page_num)

def parse(name):
    files = glob.glob("%s/%s-*html" % (html_dir,name))
    parsed_rows = []
    for file in files:
        with open(file) as fh:
            print("parsing %s" % file)
            html = fh.read()
            soup = BeautifulSoup(html)
            table = soup.find("table")
            rows = table.findAll('tr')
            for row in rows[1:-1]:
                parsed_rows.append(parse_row(row))

    #sort
    from datetime import datetime
    print("sorting")
    parsed_rows = sorted(parsed_rows, key=lambda x: datetime.strptime(x[1],'%Y-%m-%d'))

    print("writing")
    with open("%s/%s.csv" % (csv_dir,name), 'w') as csvfile:
        pin_csv = csv.writer(csvfile)
        for row in parsed_rows:
            pin_csv.writerow(row)


def parse_row(row):
    cols = row.findAll('td')
    currency,cost = cols[0].getText().split(' ')
    raw_date = cols[2].getText()
    #TODO get rid of arrow
    date = arrow.get(raw_date, 'DD MMMM, YYYY')

    cost=''.join(i for i in cost if i.isdigit())
    cost = int(cost)
    return (currencies[currency]*cost,date.format('YYYY-MM-DD'))

def moving_average(x, n, type='simple'):
    """
    compute an n period moving average.

    type is 'simple' | 'exponential'

    """
    x = np.asarray(x)
    if type=='simple':
        weights = np.ones(n)
    else:
        weights = np.exp(np.linspace(-1., 0., n))

    weights /= weights.sum()


    a =  np.convolve(x, weights, mode='full')[:len(x)]
    a[:n] = a[n]
    return a

def plot(name=None):
    import matplotlib.pyplot as plt
    from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')

    fig, ax = plt.subplots()


    files = glob.glob("%s/*csv" % (csv_dir))
    if name:
        files = ["%s/%s.csv" % (csv_dir,name)]
    sum_dates = {}

    for file in files:
        dates = []
        prices = []
        print("plotting %s" % file)
        with open(file) as csvfile:
            pin_csv = csv.reader(csvfile)
            for row in pin_csv:
                date = datetime.strptime(row[1],'%Y-%m-%d')
                dates.append(date)
                date_key = datetime.strftime(date,'%Y-%m')
                price = float(row[0])
                if sum_dates.has_key(date_key):
                    sum_dates[date_key].append(price)
                else:
                    sum_dates[date_key] = [price]
                prices.append(price)

        prices = moving_average(prices,20) 

#        ax.plot_date(dates, prices, '-', label=file)


    date_list = []
    sum_prices = []
    #work out sums
    for date in sorted(sum_dates.keys()):
        num = len(sum_dates[date])
        date_list.append(datetime.strptime(date,'%Y-%m'))
        sum_prices.append(sum(sum_dates[date]) / num)

    ax.plot_date(date_list, sum_prices, '-')

    # format the ticks
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.autoscale_view()

    # format the coords message box
    ax.fmt_xdata = DateFormatter('%Y-%m-%d')
    ax.grid(True)
    fig.autofmt_xdate()
    plt.legend(loc='upper left')
    plt.show()


"""
if len(sys.argv) == 2:
    name = sys.argv[1]
else:
    name = None
"""

#machines = get_machines(1,12)
"""
with open("machines.txt") as fh:
    machines = fh.readlines()
for machine in machines[85:100]:
    machine = machine.strip()
    print("working on %s" % machine)
    fetch(machine)
    parse(machine)
"""
plot()

