import functools
import math
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

COLORS = ['#c4b61b','#1976D2','#B71C1C']

def plotGraph(dataFiles,out,XLabel,YLabel,title,X="C",Y="F"):
    # set theme
    sns.set_theme()
    # plot config
    plt.figure(figsize=(10, 3))
    ax = plt.axes()


    # Load data
    for i, file in enumerate(dataFiles):
        data = pd.read_csv(file)
        # print("{} => {} => {}".format(file,i,COLORS[i]))
        plt.plot(data[X], data[Y], label = str(file).split('.')[0], color=COLORS[i], linewidth=1.5)

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