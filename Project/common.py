import geopandas as gpd
import pandas as pd

def save_data(data, filename):
    try:
        data.to_csv(f'data/csv_ready/{filename}.csv')
    except OSError:
        print('Error saving file')


def extract_coords(row):
    if row.geometry.type == 'Polygon' or row.geometry.type == 'MultiPolygon':
        # Extract exterior coordinates for Polygon and MultiPolygon
        coords = list(row.geometry.exterior.coords)
    elif row.geometry.type == 'Point':
        coords = [(row.geometry.x, row.geometry.y)]
    else:
        # For LineString or other geometry types
        coords = list(row.geometry.coords)
    return coords

def convert_geodata_to_csv():
    # Load the shapefile using geopandas
    gdf = gpd.read_file('data/gshhs/GSHHS_shp/l/GSHHS_l_L1.shp')

    # If the geometry is not a single point but polygons or linestrings, you will need to explode them:
    gdf = gdf.explode(index_parts=True)

    # Convert the geometry to x, y coordinates
    # Apply the function to create a new column with coordinates
    gdf['coords'] = gdf.apply(extract_coords, axis=1)

    # Now, we will explode the coordinates list into separate rows to handle multiple points
    gdf_exploded = gdf.explode('coords', ignore_index=True)

    # Split the coordinate tuples into separate columns
    gdf_exploded[['lon', 'lat']] = pd.DataFrame(gdf_exploded['coords'].tolist(), index=gdf_exploded.index)

    # Drop the now-unnecessary 'coords' column
    gdf_exploded = gdf_exploded.drop(columns=['coords'])

    gdf_exploded.to_csv('data/csv_ready/gdf_csv.csv', index=False)

    print(gdf_exploded)

if __name__ == '__main__':
    convert_geodata_to_csv()