import numpy as np
import pandas as pd
import xarray as xr
import os
import netCDF4

from Project.common import save_data


def round_to_nearest_half(x):
    """ the function returns the value rounded to the nearest half """
    return np.round(x * 2) / 2


def convert_to_datetime(date):
    """ converts and normalize the Timestamp obj """
    date = pd.to_datetime(date)  # convert the string to pd.Timestamp object
    date = date.normalize()  # normalize timestamp

    return date


def extract_date(dataset):
    """ the function extracts the date from the dataset, converts it to datetime object and returns it normalized """
    date = dataset.attrs['time_coverage_start']  # extract the date from the dataset

    return convert_to_datetime(date)


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


def dataset_to_csv(filename, array):
    """ the function accepts list of datasets and concatenate them into one single .csv file while
    extracts the SST and joins the date index
    coordinates denotes the start-end point (lat,lon)
    """

    complete_data = pd.DataFrame([])  # creating empty dataframe

    # extracting to pandas dataframe
    for dataset in array:
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

        df_sst['lon'] = np.where(df_sst['lon'] < 0, df_sst['lon'] + 360, df_sst['lon'])  # adjusting for negative long
        df_sst.sort_values(['lat', 'lon'])

        ds_date = extract_date(dataset)
        df_sst.index = pd.Index([ds_date] * len(df_sst))
        complete_data = pd.concat([complete_data, df_sst])

    save_data(complete_data, filename)

    return complete_data


def read_files(directory_name, ext):
    """
    Function that walks through a specified directory, reads all .nc/.csv files,
    and extract the dataset to a list if required, and return them within a single list object.

    :param directory_name: path to the directory
    :param ext: takes file extension, 'csv' or 'nc'
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
            if file.lower().endswith(f'.{ext}'):
                full_path = os.path.join(root, file)
                try:
                    if ext == 'nc':
                        with xr.open_dataset(f'{full_path}', engine='netcdf4') as nc_file:
                            result.append(nc_file)
                    elif ext == 'csv':
                        result.append(pd.read_csv(f'{full_path}', header=None))
                except Exception as e:
                    print(f'Failed to read {full_path}: {e}')
    return result


def clean_csvs(filename, array, start_date):
    """
    the function will clean the dataframe preparing for plotting and analysis and concatenate to a single csv file

    :param filename: name of file to save
    :param array: list of dataframes
    :param start_date: date/month of starting the dataframe collection in format YYYY-MM
    :return: list of pd.DataFrame compiled, cleand data
    """

    complete_data = pd.DataFrame([])  # creating empty dataframe

    # creating the range of the latitude and longitude
    lat = np.arange(-90, 90, 0.5)
    lon = np.arange(-180, 180, 0.5)

    start_date = convert_to_datetime(start_date)

    for i, df in enumerate(array):
        # renaming values to math the longitude and adding column matching the latitude
        df.columns = lon
        df['lat'] = lat

        # transposing the longitude to column and extracting the SST to a separate column
        df = df.melt(id_vars='lat', var_name='lon', value_name='sst')

        # filtering the coordinates dataset
        df = filter_coordinates(df)
        df = df.reset_index(drop=True)

        df['lon'] = np.where(df['lon'] < 0, df['lon'] + 360, df['lon'])  # adjusting for negative long
        df.sort_values(['lat', 'lon'])

        df.sst = df.sst.apply(lambda x: None if x > 100 else x)  # cleaning the non-valid data
        df = df.dropna()

        df_date = start_date + pd.DateOffset(months=i)
        df.index = pd.Index([df_date] * len(df))

        complete_data = pd.concat([complete_data, df])

    save_data(complete_data, filename)

    return complete_data



def csv_from_avhrp_csv(directory_name, output_file, start_date):
    """
    Passes the .csv in provided dirname, cleans and arranges the data

    :param directory_name: path to the directory
    :param output_file: filename of the output compiled csv
    :param start_date: indicate YYYY-MM of start of the dataframe. pass as indicated
    :return: list of pd.Dataframe objects
    """

    dataset_array = read_files(directory_name, ext='csv')
    compiled_data = clean_csvs(output_file, dataset_array, start_date)

    return compiled_data


def csv_from_aqua_modis_dataset(directory_name, output_file):
    """
    Passes the .nc in provided dirname, cleans and arranges the data

    :param directory_name: path to the directory
    :param output_file: filename of the output compiled csv
    :return: list of pd.Dataframe objects
    """
    dataset_array = read_files(directory_name, ext='nc')
    compiled_data = dataset_to_csv(output_file, dataset_array)

    return compiled_data


def create_urls():
    result = []

    base_url = "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/AQUA_MODIS.{start_date}_{end_date}.L3m.MO.SST.sst.9km.nc"
    # https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/AQUA_MODIS.20230101_20230131.L3m.MO.SST.sst.9km.nc

    start = pd.to_datetime('20020101')
    offset = pd.DateOffset(months=1)
    day = pd.Timedelta(days=1)

    while True:
        month_start = start.strftime('%Y%m%d')
        start += offset
        month_end = (start - day).strftime('%Y%m%d')

        url = base_url.format(start_date=month_start, end_date=month_end)
        result.append(url)

        with open('urls.txt', 'a') as file:
            file.write(url + '\n')

        if start.year == 2023:
            break

    return result
