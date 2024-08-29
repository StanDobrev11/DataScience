import numpy as np
import pandas as pd
import xarray as xr
import os
import netCDF4


def round_to_nearest_half(x):
    """ the function returns the value rounded to the nearest half """
    return np.round(x * 2) / 2


def extract_date(dataset):
    """ the function extracts the date from the dataset, converts it to datetime object and returns it normalized """

    date = dataset.attrs['time_coverage_start']  # extract the date from the dataset
    date = pd.to_datetime(date)  # convert the string to pd.Timestamp object
    date = date.normalize()  # normalize timestamp

    return date


def generate_coordinates_filter_query(coordinates):
    """ extracts the lat and long for the filter query """
    for point in coordinates:
        pass


def filter_coordinates(df):
    # filtering lat[20S; 20N]
    df = df[(df['lat'] >= -20) & (df['lat'] <= 20)]

    # filtering long[130E -> 180 -> -80 W]
    df = df[(df.lon >= -180) & (df.lon <= -80) | (df.lon >= 130) & (df.lon <= 180)]

    return df


def create_dataframe(*args, **kwargs):
    """ the function accepts list of datasets and concatenate them into one single .csv file while
    extracts the SST and joins the date index
    coordinates denotes the start-end point (lat,lon)
    """

    complete_data = pd.DataFrame([])  # creating empty dataframe

    # extracting to pandas dataframe
    for dataset in args:
        df_sst = dataset['sst'].to_dataframe()
        df_sst.reset_index(inplace=True)  # dropping the multiindex
        df_sst = filter_coordinates(df_sst)  # filtering the dataset basis target coordinates
        df_sst = df_sst.dropna()  # dropping na values

        # rounding lats and long to 0.5 deg
        df_sst.lat = df_sst.lat.apply(round_to_nearest_half)
        df_sst.lon = df_sst.lon.apply(round_to_nearest_half)

        df_sst = df_sst.groupby(['lat', 'lon']).sst.mean()  # grouping by lat and long and averaging the sst
        df_sst = df_sst.reset_index()  # dropping the multiindex

        df_sst.sst = df_sst.sst.apply(lambda x: round(x, 1))  # rounding the sst

        ds_date = extract_date(dataset)
        df_sst.index = pd.Index([ds_date] * len(df_sst))
        complete_data = pd.concat([complete_data, df_sst])

    complete_data.to_csv('data/csv/test_csv.csv')

    return complete_data


def extract_datasets(directory_name, filename=None):
    """
    Function that walks through a specified directory, reads all .nc files,
    and extract the dataset to a list.
    """
    result = []

    # Get the full path of the directory
    current_dir = os.getcwd()
    directory_path = os.path.join(current_dir, directory_name)

    if not os.path.isdir(directory_path):  # Check if the directory exists
        print(f'The directory {directory_name} does not exist in the current working directory.')
        return

    for root, dirs, files in os.walk(directory_name):  # Walk through the directory
        for file in files:
            if file.endswith('.nc'):
                full_path = os.path.join(root, file)
                try:
                    with xr.open_dataset(f'{full_path}', engine='netcdf4') as nc_file:
                        result.append(nc_file)  # Appends the dataset to the result list
                except Exception as e:
                    print(f'Failed to read {full_path}: {e}')
    return result


if __name__ == '__main__':
    result_list = extract_datasets('data/aqua_modis/elnino/2015')
    df = create_dataframe(result_list[0])
