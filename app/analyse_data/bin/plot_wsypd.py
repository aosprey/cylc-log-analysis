#!/usr/bin/env python

import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime


def view_canari(suite_file='suite_perf.csv', plot_file='wsypd.png'):
    """ 
    Plot speeds of ARCHER2 runs
    """
    data = pd.read_csv(suite_file)
    nyears = int(data['Run progress (years)'].sum())
    date = datetime.today().strftime('%Y-%b-%d')
    ax=data.plot.scatter('SYPD','ASYPD')
    ax.set_title(f"CANARI speeds as of {date}\n(Red star is average for {nyears} simulated years)")

    # get weighted average of speeds (weighted by years per simulation)
    data['WSYPD'] = data['SYPD']*data['Run progress (years)']
    data['WASYPD'] = data['ASYPD']*data['Run progress (years)']
    asypd = data['WASYPD'].sum()/nyears
    sypd = data['WSYPD'].sum()/nyears

    ax.plot(sypd,asypd,marker='*', color='red',markersize=10)
    plt.savefig(plot_file)


if __name__=="__main__":

    DATA_DIR = '/gws/nopw/j04/canari/public/perf_analysis'
    SUITE_FILE = DATA_DIR + '/DATA/suite_perf.csv'
    PLOT_FILE = DATA_DIR + '/IMAGES/coupled_wsypd.png'
    
    view_canari(SUITE_FILE, PLOT_FILE)
