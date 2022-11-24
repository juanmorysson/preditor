import numpy as np
import rasterio
from .models import Raster
import os

def ndvi(srcRed, srcNearInRed):
	bandRed = srcRed.read(1)
	bandNir = srcNearInRed.read(1)
	ndvi = np.zeros(srcRed.shape, dtype=rasterio.float32)
	ndvi = (bandNir.astype(float)-bandRed.astype(float))/(bandNir+bandRed)
	return ndvi

def ndvi_write(ndvi, srcRed, url, name = 'ndvi'):
	kwargs = srcRed.meta
	kwargs.update(
	    dtype=rasterio.float32,
	    driver='GTiff',
	    count=1,
	    compress='lzw')
	with rasterio.open(url+name+'.tif', 'w', **kwargs) as dst:
	    dst.write(ndvi.astype(rasterio.float32), 1)

def indice_write_tif(raster, srcRef, path, filename):
	kwargs = srcRef.meta
	kwargs.update(
	    dtype=rasterio.float32,
	    driver='GTiff',
	    count=1,
	    compress='lzw')
	with rasterio.open(path+filename+'.tif', 'w', **kwargs) as dst:
		dst.write(raster.astype(rasterio.float32), 1)

def indice_calc_formula(srcRef, sat, formula, path):
	print("separando formula......")
	list = formula.split()
	list_r = []
	for char in list:
		if len(char) > 1:
			if list_r.__contains__(char):
				continue
			else:
				list_r.append(char)
			print(char)
	myVars = vars()
	for item in list_r:
		name = Raster.objects.get(tagOnSat=item, satelite = sat).band
		linha = " rasterio.open('"+path+"\\cortes\\"+name+".tif').read(1)"
		linha = linha.replace("\\","\\\\")
		myVars[item] = eval(linha)

	print("executando......")
	raster = np.zeros(srcRef.shape, dtype=rasterio.float32)
	formula = formula.replace("−", "-")
	raster = eval(formula)
	print("pronto......")
	return raster

