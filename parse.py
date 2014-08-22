import arrow
import numpy as np
import csv
import time
import glob
from currencies import currencies
from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import re

#fetchs all available pages and saves them as html files
def fetch(name='Doctor-Who'):
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
            with open('%s-%s.html' % (name,page_num),'w') as fh:
                fh.write(html)
            time.sleep(1)
    except Exception:
        print("finished at page %s" % page_num)

def parse(name='Doctor-Who'):
    files = glob.glob(name + '*html')
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
    with open(name + '.csv', 'w') as csvfile:
        pin_csv = csv.writer(csvfile)
        for row in parsed_rows:
            pin_csv.writerow(row)


def parse_row(row):
    cols = row.findAll('td')
    currency,cost = cols[0].getText().split(' ')
    raw_date = cols[2].getText()
    date = arrow.get(raw_date, 'DD MMMM, YYYY')

#    import ipdb; ipdb.set_trace()
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

def plot(name):
    import matplotlib.pyplot as plt
    from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')

    dates = []
    prices = []
    from datetime import datetime
    with open(name + '.csv') as csvfile:
        pin_csv = csv.reader(csvfile)
        for row in pin_csv:
            dates.append(datetime.strptime(row[1],'%Y-%m-%d'))
            prices.append(float(row[0]))

    prices = moving_average(prices,20) 

    fig, ax = plt.subplots()
    ax.plot_date(dates, prices, '-')

    # format the ticks
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.autoscale_view()

    # format the coords message box
    ax.fmt_xdata = DateFormatter('%Y-%m-%d')
    ax.grid(True)
    fig.autofmt_xdate()
    plt.show()


#name = 'Twilight-Zone'
#name = 'Doctor-Who'
name = 'Attack-from-Mars'
fetch(name)
parse(name)
plot(name)


