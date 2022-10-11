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

import csv
import requests
import pickle
import config

# Create folders
if not os.path.isdir('./mpt_imgs'):
    os.makedirs('./mpt_imgs')
if not os.path.isdir('./mpt_imgs/created_geotiffs'):
    os.makedirs('./mpt_imgs/created_geotiffs')
if not os.path.isdir('./mpt_imgs/exist_geotiffs_in_img'):
    os.makedirs('./mpt_imgs/exist_geotiffs_in_img')
collection_df = pd.read_csv('./csvs/georef_collections.csv')
collections = list(set(collection_df['collection']))
for c in collections:
    c_path = './mpt_imgs/created_geotiffs/' + c
    if not os.path.isdir(c_path):
        os.makedirs(c_path)

# For external drive find path ls -la /Volumes
# Add into '/Volumes/***/'
# '/Volumes/FAT32/'
img_paths = []
for (dirpath, dirnames, filenames) in walk('./georef_tiffs'):
    for f in filenames:
        if f[-3:] == 'jpg':
            img_paths.append(os.path.join(dirpath, f))
        elif f[-3:] == 'tif':
            p = os.path.join(dirpath, f)
            # Is this not a geotiff?
            info = gdal.Info(p, format='json')
            if info['coordinateSystem']['wkt'] != '':
                # copy file to mpt_imgs
                shutil.copy(p, './mpt_imgs/exist_geotiffs_in_img/' + os.path.basename(p))
            else:
                img_paths.append(p)
print(img_paths)


# headers = {'Authorization': 'Token ' + config.georef_key}
#
# mapids = []
# for map in maps:
#     r = requests.get('http://api.oldmapsonline.org/1.0/maps/external/' + map[0], headers=headers)
#     map.append(r.json()['id'])
#     mapids.append(map)
#
# georefs = []
# for mapid in mapids:
#     r = requests.get('http://api.oldmapsonline.org/1.0/maps/' + mapid[4] + '/georeferences', headers=headers)
#     georef = r.json()['items'][0]
#     georef['external_id'] = mapid[0]
#     georefs.append(georef)
#
# # with open(f'./osd_georefs.pickle','wb') as out_pickle:
# #   pickle.dump(georefs,out_pickle)
