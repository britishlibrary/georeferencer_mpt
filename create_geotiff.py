import numpy as np
import gdal
import osr
import rasterio
from rasterio.plot import show_hist
import pandas as pd

import pdb

from pathlib import Path, PureWindowsPath
import os
import shutil
from os import listdir
from os.path import isfile, join
from os import walk

import csv
import requests
import pickle
import config

from PIL import Image
from PIL import ImageDraw

# Create folders
if not os.path.isdir('./mpt_outs'):
    os.makedirs('./mpt_outs')
if not os.path.isdir('./mpt_outs/created_geotiffs'):
    os.makedirs('./mpt_outs/created_geotiffs')
if not os.path.isdir('./mpt_outs/exist_geotiffs_in_img'):
    os.makedirs('./mpt_outs/exist_geotiffs_in_img')
if not os.path.isdir('./georef_imgs_del/cuts/'):
    os.makedirs('./georef_imgs_del/cuts/')
if not os.path.isdir('./georef_imgs_del/gcps/'):
    os.makedirs('./georef_imgs_del/gcps/')

collection_df = pd.read_csv('./csvs/georef_collections.csv', usecols=['id', 'collection'])
collections = list(set(collection_df['collection']))
for c in collections:
    c_path = './mpt_outs/created_geotiffs/' + c
    if not os.path.isdir(c_path):
        os.makedirs(c_path)

# For external drive find path ls -la /Volumes
# Add into '/Volumes/***/'
# '/Volumes/FAT32/'
img_paths = []
# Check if image
for (dirpath, dirnames, filenames) in walk('./georef_imgs'):
    for f in filenames:
        if f[-3:] == 'jpg':
            img_paths.append(os.path.join(dirpath, f))
        elif f[-3:] == 'tif':
            p = os.path.join(dirpath, f)
            # Is this not a geotiff?
            info = gdal.Info(p, format='json')
            if info['coordinateSystem']['wkt'] != '':
                # copy file to mpt_outs
                shutil.copy(p, './mpt_outs/exist_geotiffs_in_img/' + os.path.basename(p))
            else:
                img_paths.append(p)

id_path_df = pd.read_csv('./csvs/klokan_id_path.csv')
# Deal with Windows path PureWindowsPath(p).name to get name from original
id_path_df['path'] = [PureWindowsPath(p).as_posix() for p in id_path_df['path']]
id_path_df['filename'] = [Path(p).name for p in id_path_df['path']]

# Align Img paths with Klokan_id_Path filenames
img_path_df = pd.DataFrame({'path_img': img_paths})
img_path_df['filename'] = [Path(p).name for p in img_path_df['path_img']]
id_path_df = id_path_df.merge(img_path_df, how='left', on='filename')
id_path_df = id_path_df.merge(collection_df, how='left', on='id')

def cutImg(img_path, filename, georef):
    img = Image.open(img_path)
    mask=Image.new('L', img.size, color=0)
    draw=ImageDraw.Draw(mask)

    points = tuple(tuple(sub) for sub in georef['cutline'])
    draw.polygon((points), fill=255)
    img.putalpha(mask)

    rgb = Image.new('RGB', img.size, (255, 255, 255))
    rgb.paste(img, mask=img.split()[3])
    rgb.save('./georef_imgs_del/cuts/' + filename, 'TIFF', resolution=100.0)

def createGcps(coords):
    gcps = []
    for coord in coords:
        # 'coord' = {'location': [-3.756732387660781, 50.57983418053561], 'pixel': [2164, 966]}
        col = coord['pixel'][0]
        row = coord['pixel'][1]
        x = coord['location'][0]
        y = coord['location'][1]
        z = 0
        gcp = gdal.GCP(x, y, z, col, row)
        gcps.append(gcp)
    return gcps

# https://stackoverflow.com/questions/55681995/how-to-georeference-an-unreferenced-aerial-imgage-using-ground-control-points-in

def addGcps(filename, gcps):
    # os.mkdir('./osds_tiffs_cut/')
    src = './georef_imgs_del/cuts/' + filename
    dst = './georef_imgs_del/gcps/' + filename
    # Create a copy of the original file and save it as the output filename:
    shutil.copy(src, dst)
    # Open the output file for writing for writing:
    ds = gdal.Open(dst, gdal.GA_Update)
    # Set spatial reference:
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(4326)

    # Apply the GCPs to the open output file:
    ds.SetGCPs(gcps, sr.ExportToWkt())

    # Close the output file in order to be able to work with it in other programs:
    ds = None

def createGeoTiff(src_filename, dst_path):
    src = './georef_imgs_del/gcps/' + src_filename
    dst = './mpt_outs/created_geotiffs/' + dst_path
    dst = dst.replace('jpg', 'tif')
    input_raster = gdal.Open(src)
    gdal.Warp(dst,input_raster,dstSRS='EPSG:4326',dstNodata=255)


collection = 'other'
for i, row in id_path_df.iterrows():
    if isinstance(row['path_img'], str):
        if row['path_img'] != '':
            headers = {'Authorization': 'Token ' + config.georef_key}
            r = requests.get('http://api.oldmapsonline.org/1.0/maps/external/' + row['id'], headers=headers)
            if 'id' in r.json():
                r = requests.get('http://api.oldmapsonline.org/1.0/maps/' + r.json()['id'] + '/georeferences', headers=headers)
                georef = r.json()['items'][0]
                coords = georef['gcps']

                cutImg(row['path_img'], row['filename'], georef)
                gcps = createGcps(coords)
                addGcps(row['filename'], gcps)
                # TODO Change filename to ID where necessary and add in collection folder
                create_geotiffs_path = './mpt_outs/created_geotiffs/' + row['filename']
                createGeoTiff(row['filename'], row['filename'])

            else:
                print('api problem')
                # print(r.json())

    # # with open(f'./osd_georefs.pickle','wb') as out_pickle:
    # #   pickle.dump(georefs,out_pickle)
# id_path_df.to_csv('./id_path_df.csv', index = False)

# Remove unused collection folders
for c in collections:
    c_path = './mpt_outs/created_geotiffs/' + c
    if len(os.listdir(c_path)) == 0: # Check if the folder is empty
        shutil.rmtree(c_path)
shutil.rmtree('./georef_imgs_del/cuts/')
shutil.rmtree('./georef_imgs_del/gcps/')
