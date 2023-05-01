#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd

def fetch_data(url):
    """
    fetches data from `url` and marshals into pandas dataframe `df`

    looks like this:
             station_name  latitude  longitude  reading_2023-04-30T08:45:00+08:00
    0         Banyan Road   1.25600  103.67900                               90.6
    1       Clementi Road   1.33370  103.77680                               87.6
    2      Nanyang Avenue   1.34583  103.68166                               88.2
    3          Pulau Ubin   1.41680  103.96730                               92.3
    4             Sentosa   1.25000  103.82790                               74.2
    5  West Coast Highway   1.28100  103.75400                               86.9
    """
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
        self.refresh_interval = 5*60*1000  # 5 minutes
        self.title("Relative Humidity Visualizer")
        self.df = pd.DataFrame()
        
        # create notebook GUI
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        # initialize graphs
        graphs = [self.ScatterPlot(), self.BarPlot(), self.LinePlot()]
        for graph in graphs:
            self.create_tab(notebook, graph.fig)

        self.update_graphs(graphs)

    def update_graphs(self, graphs=None):
        """
        fetches new data and updates the `graphs`
        """
        df = fetch_data(self.url)
        df.drop([col for col in df.columns if col.startswith('reading_') and col in self.df.columns], axis=1, inplace=True)
        self.df = df if self.df.empty else self.df.merge(df, on=['station_name', 'latitude', 'longitude'], suffixes=('','_'))
        for graph in graphs:
            graph.plot(self.df)
        self.update()
        self.after(self.refresh_interval, self.update_graphs, graphs)

    def create_tab(self, notebook, fig, title=None):
        """
        creates a tab in `notebook` with figure `fig`
        """
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
            self.ax.clear()
            
            reading = df.columns[-1]
            scatter = self.ax.scatter(df['longitude'], df['latitude'], c=df[reading], cmap=self.cmap)

            if self.cbar is None:
                self.cbar = plt.colorbar(scatter)
                self.cbar.set_label(self.cbarlabel)
            else:
                self.cbar.update_normal(scatter)

            # label the points
            min_val = df[reading].min()
            max_val = df[reading].max()
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
            self.fig.canvas.draw()

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
            self.ax.clear()

            reading = df.columns[-1]
            bars = self.ax.bar(df['station_name'], df[reading])

            # label maximum and minimum
            labels = []
            min_val = df[reading].min()
            max_val = df[reading].max()
            for value in df[reading]:
                label = str(value)
                if value == max_val:
                    label += ' <max>'
                elif value == min_val:
                    label += ' <min>'
                labels.append(label)
            self.ax.bar_label(bars, labels=labels)
            self.fig.canvas.draw()

            return self.fig

    class LinePlot:
        def __init__(self, title='Relative Humidity over Time', xlabel='Time', ylabel='Relative Humidity (%)', linewidth=2):
            self.title = title
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.ylabel)
            self.ax.set_title(title)
            self.lines = {}
            self.linewidth = linewidth
            self.axhmin_line = None
            self.axhmax_line = None

        def plot(self, df):
            reading_cols = [col for col in df.columns if col.startswith('reading_')]
            reading_labels = pd.to_datetime([col.lstrip('reading_') for col in reading_cols])
            for i, station in df.iterrows():
                station_name = station['station_name']
                if station_name not in self.lines:
                    self.lines[station_name], = self.ax.plot(reading_labels, station[reading_cols],
                                                             label=station_name, marker='o',
                                                             linewidth=self.linewidth)
                else:
                    self.lines[station_name].set_data(reading_labels, station[reading_cols])

            if len(reading_labels) > 1:
                self.ax.set_xlim(reading_labels.min(), reading_labels.max())

            self.ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 5)))

            # label maximum and minimum over timespan
            min_val = df[reading_cols].min().min()
            max_val = df[reading_cols].max().max()
            if self.axhmin_line is None:
                self.axhmin_line = self.ax.axhline(min_val, linestyle='--', color='black')
            else:
                self.axhmin_line.set_ydata([min_val, min_val])
            if self.axhmax_line is None:
                self.axhmax_line = self.ax.axhline(max_val, linestyle='--', color='black')
            else:
                self.axhmax_line.set_ydata([max_val, max_val])
            self.ax.set_yticks([max_val, min_val], labels=[f'{max_val} <max>', f'{min_val} <min>'], minor=True)
            self.ax.legend()
            self.fig.canvas.draw()

            return self.fig

if __name__ == '__main__':
    app = HumidityVisualizer()
    app.mainloop()
