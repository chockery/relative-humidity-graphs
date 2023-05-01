# Relative Humidity in Singapore
This Python script fetches relative humidity data from [Singstat](https://api.data.gov.sg/v1/environment/relative-humidity) and visualizes it with a scatter plot, bar graph, and line graph.

## Installation
Should work on any OS (tested on Alpine and Windows 10)

To install the required Python packages, run:
```
pip install tkinter matplotlib pandas
```

## Usage
To run the script:
```
python relative_humidity.py
```
You should see a new window pop up with 3 tabs.

### Scatterplot of Stations
This shows a scatterplot of each weather station's location, with the points coloured according to the latest relative humidity readings.
Maximum and minimum reading values are indicated with ``<max>`` and ``<min>`` respectively.

### Relative Humidity at Each Station
This shows a bar graph of the humidity readings at each station. Maximum and minimum values are tagged similar to the above.

### Relative Humidity over Time
This shows a live line graph of all humidity readings since the start of the script. Maximum and minimum historical values are marked by the black dotted lines.
