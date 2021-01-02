import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import os.path
from PIL import Image, ImageOps
from otsu import run
from stonk import get_data

def graph(src):

    if not os.path.isfile(f"../graphs/charts/{src}.tsv"):
        run(src)
        img = Image.open(f"../segmented/{src}")
        img = ImageOps.grayscale(img)
        img = np.asarray(img)
        rows, cols = img.shape
        graph_img = np.zeros((rows, cols))
        graph = np.zeros(cols)

        print("Graphing City...")

        for j in np.arange(cols):
            for i in np.arange(rows):
                if img[i, j] == 0:
                    graph_img[i, j] = 255
                    graph[j] = rows - i
                    break

        np.savetxt(f"../graphs/charts/{src}.tsv", graph, delimiter="\t")

        plt.plot(np.arange(cols), graph)
        plt.savefig(f"../graphs/images/{src}")
        plt.close()

    else:
        graph =  np.genfromtxt(f"../graphs/charts/{src}.tsv", delimiter="\t")

    return graph

def get_similarity(data1, data2):
    length = min(len(data1), len(data2))

    percents = np.zeros(length)
    for i in np.arange(length):
        percents[i] = 100 * np.absolute((data1[i] - data2[i])) / data1[i]

    return 100 - np.mean(percents)

def graph_stonk(city, ticker, period, start, end):
    data = get_data(ticker, period, start, end)
    date_index = data.index

    city_graph = graph(f"{city}.jpg")
    train_length = int(0.6 * len(city_graph))
    train_graph = city_graph[:train_length]
    test_graph = city_graph[train_length:]
    
    diff = len(city_graph) - train_length

    length_scale = (len(date_index) / train_length)

    print("Graphing Stock...")

    data = data.reset_index()

    if length_scale > 1:
        length_scale = np.ceil(length_scale)
        data = data[data.index % length_scale == 0]
        data = data.reset_index()
        data = data.drop('index', axis=1)

    if length_scale < 1:

        length_scale = ( 1.0 / length_scale)
        length_scale = int(length_scale)
        indicies = np.arange(0, train_length, length_scale, dtype='int64')
        train_graph = np.take(train_graph, indicies)

        indicies = np.arange(0, diff, length_scale, dtype='int64')
        test_graph = np.take(test_graph, indicies)

    train_graph = np.append(train_graph, test_graph)

    value_scale = np.median(train_graph) / data['Close'].median()
    for i in np.arange(len(train_graph)):
        train_graph[i] /= value_scale

    train_graph = pd.DataFrame(data=train_graph, columns=[city])

    more_dates = pd.date_range(data.iloc[len(data)-1]['Date'], periods = len(train_graph) -len(data), freq="D").to_series()
    dates = data['Date']
    dates = dates.append(more_dates)
    dates = pd.DataFrame(data=dates, columns=['Date']).reset_index().drop('index', axis=1)

    if len(date_index) > train_length:
        data = data.join(train_graph)
    else:
        data = train_graph.join(data)
        data = data.drop('Date', axis=1).join(dates)

    sim_graph = data.dropna()
    similarity = get_similarity(sim_graph['Close'].to_numpy(), sim_graph[city].to_numpy())
    print(f"{city} and {ticker} are {similarity} percent similar")

    data = data.set_index('Date')
    data = data.rename(columns={"Close" : ticker})

    data.plot()
    plt.show()

graph_stonk('Shanghai', 'MAR', '1d', '2020-03-01', '2020-08-24')