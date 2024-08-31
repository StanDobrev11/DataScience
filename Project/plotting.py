import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata


def plot_equatorial_pacific(df, cond_name, plot_type='cnt', vmin=None, vmax=None):
    """
    The function will plot the sequential months of SST,
    with each month's data on a separate subplot.

    :param cond_name: Taking the name of the plotted event
    :param plot_type: Defaults to contour map. Choose between contour map ['cnt'] and scatter plot ['sct'].
    :param vmin: pass the minimum scale of the temperature
    :param vmax: pass the maximum scale of the temperature
    """

    grouped_df = df.groupby(df.index)

    # Determine the number of subplots (one for each unique date)
    subplot_count = len(grouped_df)

    # Create subplots in a single row
    fig, axs = plt.subplots(1, subplot_count, figsize=(15 * subplot_count, 8))

    # If only one subplot, axs will not be an array, so we convert it to one
    if subplot_count == 1:
        axs = [axs]

    # Determine the common range for the color scale
    all_sst_values = df['sst'].values

    if vmin is None or vmax is None:
        vmin, vmax = np.min(all_sst_values), np.max(all_sst_values)

    for i, (date, data) in enumerate(grouped_df):

        if plot_type == 'sct':
            subplot = axs[i].scatter(data.lon, data.lat, c=data.sst, cmap='jet', alpha=0.7, s=150, vmin=vmin, vmax=vmax)

        else:
            lon_grid = np.linspace(data.lon.min(), data.lon.max(), 100)
            lat_grid = np.linspace(data.lat.min(), data.lat.max(), 100)
            lon_grid, lat_grid = np.meshgrid(lon_grid, lat_grid)
            sst_grid = griddata((data.lon, data.lat), data.sst, (lon_grid, lat_grid), method='linear')

            subplot = axs[i].contourf(lon_grid, lat_grid, sst_grid, cmap='jet', levels=20, vmin=vmin, vmax=vmax)

        fig.colorbar(subplot, ax=axs[i], label='Temperature')

        x_tick = np.arange(130, 290, 10)
        x_label = [f'{x}°E' if x <= 180 else f'{360 - x}°W' for x in x_tick]

        y_tick = np.arange(-20, 25, 5)
        y_label = [f'{np.abs(x)}°S' if x < 0 else f'{np.abs(x)}°N' for x in y_tick]

        axs[i].add_patch(plt.Rectangle((190, -5), 50, 10, linewidth=2, edgecolor='red', facecolor='none'))

        axs[i].axhline(y=0)

        axs[i].set_xticks(ticks=x_tick)
        axs[i].set_xticklabels(labels=x_label)

        axs[i].set_yticks(ticks=y_tick)
        axs[i].set_yticklabels(labels=y_label)

        axs[i].set_xlim(130, 280)
        axs[i].set_ylim(-20, 20)
        axs[i].set_xlabel('Longitude')
        axs[i].set_ylabel('Latitude')
        axs[i].set_title(f'{cond_name} SST for {pd.to_datetime(date).strftime("%B %Y")}')

    plt.tight_layout()
    plt.show()
