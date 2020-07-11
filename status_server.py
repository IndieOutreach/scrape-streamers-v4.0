# ==============================================================================
# About: status_server.py
# ==============================================================================


# Imports ----------------------------------------------------------------------

# system imports
import sys
import json

# matplotlib and charting imports
import base64
from io import BytesIO
from matplotlib import pyplot as plt

# flask imports
from flask import Flask, render_template       # <- Flask/Server Imports

# IndieOutreach imports
from db_manager import *


# Constants --------------------------------------------------------------------

app = Flask(__name__)
#plt.subplots_adjust(bottom=0.05, top=1, left=0.05, right=1)


# Routes -----------------------------------------------------------------------

@app.route("/")
def empty_route():
    charts = []
    #charts.append(get_chart('Title', [1, 2, 3, 4, 5], [0, 2, 1, 3, 4]))
    charts = get_count_charts()
    return render_template('home.html', charts=charts)


# Functions --------------------------------------------------------------------

def get_count_charts():
    charts = []
    current_time = int(time.time())
    db = CountLogDB()
    prev_counts = db.get_all_counts_since(1 * 60 * 60 * 24 * 7) # <- 1 week

    for table_name, counts in prev_counts.items():
        x = []
        y = []
        max = 0
        for count in counts:
            val = abs(count['date_scraped'] - current_time)
            max = val if (val > max) else max

        for count in counts:
            t = max - abs(count['date_scraped'] - current_time)
            x.append(t / 10000)
            y.append(count['count'])

        xobj = {'data': x, 'label': 'Time ->'}
        yobj = {'data': y, 'label': 'COUNT(*)'}
        charts.append(get_chart(f"COUNT(*) from twitch.{table_name} - last 7 days", xobj, yobj))
    return charts


def get_chart(title, x, y):
    img = BytesIO()
    plt.plot(x['data'], y['data'])
    plt.xlabel(x['label'])
    plt.ylabel(y['label'])
    plt.title(title)
    plt.savefig(img, format='png')
    plt.close()
    plot_url = base64.encodebytes(img.getvalue()).decode('utf8')
    return {'url': plot_url, 'title': title}

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    app.run(port=4567)
