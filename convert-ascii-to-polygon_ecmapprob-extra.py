#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 18:11:31 2025
@author: ailsa naismith

This Python script works within QGIS. Its purpose is to convert outputs of 
the ECMapProb model from raster files (.asc) to a series of vector files 
associated with a range of user-defined threshold values.
For each threshold value, the script will produce these files:
    - .dbf
    - .shp
    - .shx
    - .tif
    - .tif.aux.xml
User may define the following variables:
    - Input directory (where the input files (.asc) are stored)
    - Output directory (where the output files will be saved)
    - Thresholds (the thresholded values for each of the output polygons).
Find these variables in the section 'USER-DEFINED VALUES'

***IMPORTANT***
This script runs in the QGIS Python console. 
Within QGIS, go to > Plugins > Python console and run the following command:
    
    exec(open(r"/path/to/this/script/convert-ascii-to-polygon_ecmapprob-extra.py".encode('utf-8')).read())
    
    -> Note that you must change pathname to where this script is stored in your computer!
"""

## IMPORT MODULES
import os
import numpy as np
from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsProject, QgsVectorLayer, QgsField
from PyQt5.QtCore import QVariant
import processing

##-----------------------------------------------------------------------------

## DEFINE 'CREATE THRESHOLDED RASTER' FUNCTION
# Function to create a thresholded raster layer
def create_threshold_raster(input_raster_path, output_raster_path, threshold_value):
    # Open the input raster using GDAL
    raster_ds = gdal.Open(input_raster_path)
    band = raster_ds.GetRasterBand(1)
    
    # Read raster data as array
    raster_data = band.ReadAsArray()

    # Create a mask where values are greater than or equal to the threshold
    thresholded_data = np.where(raster_data >= threshold_value, raster_data, np.nan)

    # Create an output raster with the same georeferencing as the input raster
    driver = gdal.GetDriverByName('GTiff')
    output_ds = driver.Create(output_raster_path, raster_ds.RasterXSize, raster_ds.RasterYSize,
                              1, gdal.GDT_Float32)
    output_ds.SetGeoTransform(raster_ds.GetGeoTransform())
    output_ds.SetProjection(raster_ds.GetProjection())

    # Write the thresholded data to the output raster
    output_band = output_ds.GetRasterBand(1)
    output_band.WriteArray(thresholded_data)
    output_band.SetNoDataValue(np.nan)

    # Close datasets
    output_band = None
    output_ds = None
    raster_ds = None
    
    return output_raster_path

##-----------------------------------------------------------------------------

## DEFINE 'RASTER TO VECTOR' FUNCTION
# Function to convert raster to vector (polygons)
def raster_to_vector(input_raster_path, output_vector_path):
    # Use QGIS Raster to Polygon function to convert raster to vector
    processing.run("gdal:polygonize", {
        'INPUT': input_raster_path,
        'BAND': 1,
        'FIELD': 'DN',
        'OUTPUT': output_vector_path
    })
    
##-----------------------------------------------------------------------------

## DEFINE 'VECTORIZE THRESHOLDED RASTER' FUNCTION
# Function to create threshold rasters and vectorize them
def process_thresholds(input_raster_path, output_dir, thresholds):
    vector_layers = []

    # Process each threshold
    for threshold in thresholds:
        print(f"Processing threshold: {threshold}")
        
        # Create the thresholded raster with the target CRS (if provided)
        output_raster_path = f"{output_dir}/{os.path.basename(input_raster_path).split('.')[0]}_threshold_{threshold}.tif"
        create_threshold_raster(input_raster_path, output_raster_path, threshold)
        
        # Convert the thresholded raster to vector (polygons)
        output_vector_path = f"{output_dir}/{os.path.basename(input_raster_path).split('.')[0]}_threshold_{threshold}_polygons.shp"
        raster_to_vector(output_raster_path, output_vector_path)
        
        # Load the vector layer into QGIS
        vector_layer = QgsVectorLayer(output_vector_path, f"{os.path.basename(input_raster_path).split('.')[0]}_Threshold {threshold}", "ogr")
        if vector_layer.isValid():
            QgsProject.instance().addMapLayer(vector_layer)
            vector_layers.append(vector_layer)
    
    return vector_layers

##-----------------------------------------------------------------------------

## DEFINE 'FOLDER PROCESSING LOOP' FUNCTION
# Function to process all rasters in a folder
def process_rasters_in_folder(input_dir, output_dir, thresholds):
    # Get all raster files in the input folder (filtering for .asc files)
    raster_files = [f for f in os.listdir(input_dir) if f.endswith('.asc')]

    for raster_file in raster_files:
        input_raster_path = os.path.join(input_dir, raster_file)
        print(f"Processing raster: {input_raster_path}")
        
        # Process the current raster with the thresholds and save outputs
        process_thresholds(input_raster_path, output_dir, thresholds)

##-----------------------------------------------------------------------------

## USER-DEFINED VARIABLES
# User defines input and output directories and desired threshold values:
input_dir = "/path/to/your/input/directory"      # Replace with desired input directory
output_dir = "/path/to/your/output/directory"    # Replace with desired output directory
thresholds = [0.1, 0.5, 0.9]                     # Replace with desired threshold values

##-----------------------------------------------------------------------------

## PROCESS ALL RASTERS
# Process all rasters in the input folder
process_rasters_in_folder(input_dir, output_dir, thresholds)

