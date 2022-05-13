import functools
import math
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

def plotGraph():
    # set theme
    sns.set_theme()

    # Load data
    data = pd.read_csv('rss_with.csv')
    data2 = pd.read_csv('rss_without.csv')

    # Plot
    plt.figure(figsize=(7, 5))
    x = range(len(data['C']))
    # print(x)
    ax = plt.axes()
    # plot rss data
    plt.plot(data2['C'], data2['F'], label = "RSS without agent", color='#1976D2', linewidth=1.2)
    plt.plot(data['C'], data['F'], label = "RSS with agent", color='#B71C1C', linewidth=1.5)

    # plot process data
    # plt.plot(data['C'], data['A'], label = "Proc with agent", color='#FF6F00')
    # plt.plot(data2['C'], data2['A'], label = "Proc without agent", color='#827717')

    size = math.ceil(len(data['C'])/8)
    # print(size)
    ticks = []
    for i,item in enumerate(data['C']):
        if (i==0 or i%size==0):
            ticks.append(item)

    ax.set_xticks(ticks)
    plt.xlabel('Time')
    plt.ylabel('RSS')
    plt.title('PHP - RSS vs Time')
    plt.legend(loc = 'best')

    # fill graph with color
    # plt.fill_between(data['C'], data['F'], color='#311B9288')
    # plt.fill_between(data2['C'], data2['F'], color='#88004D40')

    plt.savefig('PHP-Memory.png')
    plt.show()

# plotGraph()