'''
This script for observing shapefile (polygon)
Collects the number of vertices, area
author: Panteleev Anton, Arkhangelsk
'''
import time
import os
import gdal
import osr
import ogr

# Settings
basic_file = 'basic_epsg4326.shp'
inEPSG = 4326
outEPSG = 32637# or 4326 (area in square degrees )

report_file = 'report.csv'
minutes = 240
time_sleep = 30

aux_file = 'aux_'+basic_file[0:-4]+'_to_epsg'+str(outEPSG)+'.shp'# aux_file

def wr(str_wr):
    outfile = open(report_file,'a')
    outfile.write(str_wr+'\n')
    outfile.close()

def shapefile_info_attr(aux_file,time_marks):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(aux_file, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        FID=str(feature.GetFID()).zfill(4)
        id=str(feature.GetField('id'))
        geometry=feature.GetGeometryRef()
        # get vertex count
        wkt=geometry.ExportToWkt()
        wkt1=wkt.replace('POLYGON ((','')
        wkt2=wkt1.replace('))','')
        wkt2_list=wkt2.split(',')
        vertex_count=len(wkt2_list)-1
        # get area in m^2 and hectare if inpfile in rectangular coordinate systems
        # get area in square degress if inpfile in geographic coordinate systems
        area_get=geometry.GetArea()
        area_ga=round(area_get / 10000, 1)
        print(FID,id,area_ga,vertex_count)
        str_wr='\t'.join([str(time_marks), FID, id, str(vertex_count), str(area_get), str(area_ga)])
        wr(str_wr)
    #print(layer)
    layer.ResetReading()

# = = = = = = = = = = = = = =
# modified by https://pcjericks.github.io/py-gdalogr-cookbook/projection.html
def reproject_a_layer(inEPSG, outEPSG, basic_file):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    # input SpatialReference
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(inEPSG)
    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(outEPSG)
    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    # get the input layer
    inDataSet = driver.Open(basic_file)
    inLayer = inDataSet.GetLayer()
    # create the output layer
    outputShapefile = 'aux_'+basic_file[0:-4]+'_to_epsg'+str(outEPSG)+'.shp'# aux_file
    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)
    outDataSet = driver.CreateDataSource(outputShapefile)
    outLayer = outDataSet.CreateLayer(outputShapefile, geom_type=ogr.wkbMultiPolygon)
    # add fields
    inLayerDefn = inLayer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)
    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()
    # loop through the input features
    inFeature = inLayer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(geom)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # dereference the features and get the next input feature
        outFeature = None
        inFeature = inLayer.GetNextFeature()
    # Save and close the shapefiles
    inDataSet = None
    outDataSet = None
# = = = = = = = = = = = = =

wr('Start observing "'+aux_file+'" '+time.ctime(time.time())+' Settings: minutes '+str(minutes)+', time_sleep '+str(time_sleep)+' sec')
wr('\t'.join(['time_marks','FID','id','vertex_count','area_m^2','area_ha']))

time_marks = 0
for x in range(3 * minutes):
    reproject_a_layer(inEPSG, outEPSG, basic_file)
    shapefile_info_attr(aux_file, time_marks)
    print('= = = step '+str(x)+' = = ','time_accum', time_marks)
    time_marks = time_marks + time_sleep
    time.sleep(time_sleep)
    

