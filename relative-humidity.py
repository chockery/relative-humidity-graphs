#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd

def fetch_data(url):
    '''
    fetches data from `url` and marshals into pandas dataframe `df`

    looks like this:
             station_name  latitude  longitude  reading_2023-04-30T08:45:00+08:00
    0         Banyan Road   1.25600  103.67900                               90.6
    1       Clementi Road   1.33370  103.77680                               87.6
    2      Nanyang Avenue   1.34583  103.68166                               88.2
    3          Pulau Ubin   1.41680  103.96730                               92.3
    4             Sentosa   1.25000  103.82790                               74.2
    5  West Coast Highway   1.28100  103.75400                               86.9
    '''
    df = pd.read_json(url, lines=True, orient="Columns")
    timestamp = df['items'][0][0]['timestamp']
    stations_df = pd.json_normalize(df['metadata'][0], record_path='stations')
    items_df = pd.json_normalize(df['items'][0], record_path='readings')
    merged_df = pd.merge(stations_df, items_df, left_on='id', right_on='station_id')
    df = merged_df[['name', 'location.latitude', 'location.longitude', 'value']]
    df.columns = ['station_name', 'latitude', 'longitude', 'reading_' + timestamp ]
    return df

class HumidityVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.url = "https://api.data.gov.sg/v1/environment/relative-humidity"
        self.title("Relative Humidity Visualizer")
        self.df = pd.DataFrame()
        
        # create notebook GUI
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        # initialize graphs
        tabs = [ self.ScatterPlot(), self.BarPlot(), self.LinePlot() ]
        for graph in tabs:
            self.create_tab(notebook, graph.fig)

        self.update(tabs)

    def update(self, tabs=None):
        new_df = fetch_data(self.url)
        self.df = new_df if self.df.empty else self.df.combine_first(new_df)
        for graph in tabs:
            graph.plot(self.df)
        self.after(1*6*1000, self.update, tabs)  # refresh every 5 minutes

    def create_tab(self, notebook, fig, title=None):
        '''
        creates a tab in `notebook` with figure `fig`
        '''
        tab = ttk.Frame(notebook)
        tab.pack(fill='both', expand=True)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(canvas, tab)
        toolbar.update()
        canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
        title = title or fig.get_axes()[0].get_title()
        notebook.add(tab, text=title)
        return tab

    class ScatterPlot:
        def __init__(self, title='Scatterplot of Stations', xlabel='Longitude', ylabel='Latitude', cmap='RdBu', cbarlabel='Relative Humidity (%)'):
            self.title = title
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.cmap = cmap
            self.cbar = None
            self.cbarlabel = cbarlabel
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.ylabel)
            self.ax.set_title(title)

        def plot(self, df):
            reading = df.columns[-1]
            scatter = self.ax.scatter(df['longitude'], df['latitude'], c=df[reading], cmap=self.cmap)

            if self.cbar is None:
                self.cbar = plt.colorbar(scatter)
                self.cbar.set_label(self.cbarlabel)
            else:
                self.cbar.update_normal(scatter)

            max_val = df[reading].max()
            min_val = df[reading].min()

            # label the points
            for index, row in df.iterrows():
                value = row[reading]
                label = f"{row['station_name']} ({value}%)"
                if value == max_val:
                    label += ' <max>'
                elif value == min_val:
                    label += ' <min>'
                self.ax.annotate(label, xy=(row['longitude'], row['latitude']),
                                 xytext=(0, -15), textcoords='offset points',
                                 ha='center', va='center')
            return self.fig

    class BarPlot:
        def __init__(self, title='Relative Humidity at Each Station', xlabel='Station', ylabel='Relative Humidity (%)'):
            self.title = title
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.ylabel)
            self.ax.set_ylim([0,100])
            self.ax.set_title(self.title)

        def plot(self, df):
            reading = df.columns[-1]
            bars = self.ax.bar(df['station_name'], df[reading])

            # label maximum and minimum
            labels = []
            max_val = df[reading].max()
            min_val = df[reading].min()
            for value in df[reading]:
                label = str(value)
                if value == max_val:
                    label += ' <max>'
                elif value == min_val:
                    label += ' <min>'
                labels.append(label)

            self.ax.bar_label(bars, labels=labels)

            return self.fig

    class LinePlot:
        def __init__(self, title='Relative Humidity over Time', xlabel='Time', ylabel='Relative Humidity (%)'):
            self.title = title
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.ylabel)
            self.ax.set_title(title)

        def plot(self, df):
            # plot the readings
            for index, row in df.iterrows():
                reading_cols = [col for col in df.columns if col.startswith('reading_')]
                readings = row[reading_cols].values
                self.ax.plot(reading_cols, readings, label=row['station_name'])

            self.ax.legend()

            return self.fig

if __name__ == '__main__':
    app = HumidityVisualizer()
    app.mainloop()
