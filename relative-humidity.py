#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd

df = pd.DataFrame()

def fetch_data(url):
    '''
    fetches data from `url` and marshals into pandas dataframe `df`
    tuned for relative humidity API data
    '''
    df = pd.read_json(url, lines=True, orient="Columns")
    stations_df = pd.json_normalize(df['metadata'][0]['stations'])
    items_df = pd.json_normalize(df['items'][0], record_path='readings', meta=['timestamp'])
    merged_df = pd.merge(stations_df, items_df, left_on='id', right_on='station_id')
    df = merged_df[['name', 'location.latitude', 'location.longitude', 'value', 'timestamp']]
    df.columns = ['station_name', 'latitude', 'longitude', 'reading', 'timestamp']
    return df

def plot_scatter(df):
    '''
    plots a scatter plot of station latitude and longitude
    '''
    fig, ax = plt.subplots()
    scatter = ax.scatter(df['longitude'], df['latitude'], c=df['reading'], cmap='RdBu')
    
    cbar = plt.colorbar(scatter)
    cbar.set_label('Relative Humidity (%)')

    for index, row in df.iterrows():
         ax.annotate(f"{row['station_name']} ({row['reading']}%)", xy=(row['longitude'], row['latitude']),
                     xytext=(0, -15), textcoords='offset points',
                     ha='center', va='center')
  
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Scatterplot of Stations')
    return fig

def plot_bar(df):
    '''
    plots a bar graph of relative humidity at each station
    '''
    fig, ax = plt.subplots()
    ax.bar(df["station_name"], df["reading"])
    ax.bar_label(ax.containers[0])
    ax.set_xlabel("Station")
    ax.set_ylabel("Relative Humidity (%)")
    ax.set_ylim([0,100])
    ax.set_title("Relative Humidity at Each Station")
    return fig

def plot_line(df):
    '''
    plots a line graph of relative humidity at each station over time
    '''
    fig, ax = plt.subplots()
    ax.bar(df["timestamp"], df["reading"])
    ax.bar_label(ax.containers[0])
    ax.set_xlabel("Time")
    ax.set_ylabel("Relative Humidity (%)")
    ax.set_ylim([0,100])
    ax.set_title("Relative Humidity over Time")
    schedule.every(5).minutes.do(fetch_data, df=df)
    return fig

def create_tab(notebook, fig, title=None):
    tab = ttk.Frame(notebook)
    tab.pack(fill='both', expand=True)
    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
    toolbar = NavigationToolbar2Tk(canvas, tab)
    toolbar.update()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
    if title is None:
        title = fig.get_axes()[0].get_title()
    notebook.add(tab, text=title)
    return tab

def main():
    url = "https://api.data.gov.sg/v1/environment/relative-humidity"
    df = fetch_data(url)
    print(df)

    # Create GUI
    root = tk.Tk()
    root.title("Relative Humidity in Singapore")
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Create tabs
    create_tab(notebook, plot_scatter(df))
    create_tab(notebook, plot_bar(df))
#    create_tab(notebook, plot_line(df))

    root.mainloop()

if __name__ == '__main__':
    main()
