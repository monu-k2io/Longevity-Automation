import functools
import math
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

def plotGraph(out,XLabel,YLabel,title,X="C",Y="F",redLabel="RSS with agent",blueLabel="RSS without agent"):
    # set theme
    sns.set_theme()

    # Load data
    data = pd.read_csv('rss_with.csv') # red line
    data2 = pd.read_csv('rss_without.csv') # blue line

    # Plot
    plt.figure(figsize=(7, 4))
    x = range(len(data[X]))
    # print(x)
    ax = plt.axes()
    # plot rss data
    plt.plot(data2[X], data2[Y], label = blueLabel, color='#1976D2', linewidth=1)
    plt.plot(data[X], data[Y], label = redLabel, color='#B71C1C', linewidth=1.2)

    # plot process data
    # plt.plot(data[X], data['A'], label = "Proc with agent", color='#FF6F00')
    # plt.plot(data2[X], data2['A'], label = "Proc without agent", color='#827717')

    size = math.ceil(len(data[X])/8)
    # print(size)
    ticks = []
    for i,item in enumerate(data[X]):
        if (i==0 or i%size==0):
            ticks.append(item)

    ax.set_xticks(ticks)
    plt.xlabel(XLabel)
    plt.ylabel(YLabel)
    plt.title(title)
    plt.legend(loc = 'best')

    # fill graph with color
    # plt.fill_between(data[X], data[Y], color='#311B9288')
    # plt.fill_between(data2[X], data2[Y], color='#88004D40')

    plt.savefig(out+".png")
    plt.show()

# plotGraph()