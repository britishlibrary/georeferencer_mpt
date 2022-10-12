import numpy as np
import os
from pathlib import Path, PureWindowsPath
import gdal
import rasterio
from rasterio.plot import show_hist
import shutil
import pandas as pd

import pdb
from os import listdir
from os.path import isfile, join
from os import walk

# Create folders
if not os.path.isdir('./mpt_outs'):
    os.makedirs('./mpt_outs')
if not os.path.isdir('./mpt_outs/tiffs'):
    os.makedirs('./mpt_outs/tiffs')
if not os.path.isdir('./mpt_outs/moved_geotiffs'):
    os.makedirs('./mpt_outs/moved_geotiffs')
if not os.path.isdir('./mpt_outs/moved_geotiffs/other'):
    os.makedirs('./mpt_outs/moved_geotiffs/other')
collection_df = pd.read_csv('./csvs/georef_collections.csv')
collections = list(set(collection_df['collection']))
for c in collections:
    c_path = './mpt_outs/moved_geotiffs/' + c
    if not os.path.isdir(c_path):
        os.makedirs(c_path)

# For external drive find path ls -la /Volumes
# Add into '/Volumes/***/'
# '/Volumes/FAT32/'
paths = []
for (dirpath, dirnames, filenames) in walk('./georef_geotiffs'):
    for f in filenames:
        if f[-3:] == 'tif':
            paths.append(os.path.join(dirpath, f))

# Is this a geotiff?
geotiff_paths = []
for p in paths:
    info = gdal.Info(p, format='json')
    if info['coordinateSystem']['wkt'] == '':
        # copy file to mpt_outs
        shutil.copy(p, './mpt_outs/tiffs/' + os.path.basename(p))
    else:
        geotiff_paths.append(p)


id_path_df = pd.read_csv('./csvs/klokan_id_path.csv')
# Deal with Windows path PureWindowsPath(p).name to get name from original
id_path_df['path'] = [PureWindowsPath(p).as_posix() for p in id_path_df['path']]
id_path_df['filename'] = [Path(p).name for p in id_path_df['path']]


# Align Geotiff filenames with Klokan_id_Path filenames
geotiff_path_df = pd.DataFrame({'path_geotiff': geotiff_paths})
geotiff_path_df['filename'] = [Path(p).name for p in geotiff_path_df['path_geotiff']]
id_path_df = id_path_df.merge(geotiff_path_df, how='left', on='filename')


# Copy to folder named after collection
collection = 'other'
for i, row in id_path_df.iterrows():
    # Find collection for geotiff
    collection_row = collection_df.loc[collection_df['id'] == row['id']]
    id_collections = collection_row['collection'].values
    if len(id_collections) == 1:
        collection = id_collections[0]

    # Does filename match Klokan ID?
    if isinstance(row['path_geotiff'], str):
        if Path(row['path_geotiff']).stem == row['id']:
            filename = row['filename']
        else:
            if not os.path.isdir('./mpt_outs/moved_geotiffs/' + collection + '/id_changed'):
                os.makedirs('./mpt_outs/moved_geotiffs/' + collection + '/id_changed')
            filename = 'id_changed/' + row['id'] + '.tif'

        dst_path = './mpt_outs/moved_geotiffs/' + collection + '/' + filename
        shutil.copyfile(row['path_geotiff'], dst_path)

# Remove unused collection folders
for c in collections:
    c_path = './mpt_outs/moved_geotiffs/' + c
    if len(os.listdir(c_path)) == 0: # Check if the folder is empty
        shutil.rmtree(c_path)

# id_path_df.to_csv('./id_path_df.csv', index = False)
