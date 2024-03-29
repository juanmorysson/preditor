import pandas as pd
from django.shortcuts import get_object_or_404
from pyproj import Transformer
from django.shortcuts import redirect
from .models import Projeto, BarraProgresso, Raster, AreaModelo
from .class_utils import *
from rasterio.enums import Resampling
from PIL import Image
import sys, os, struct
import math
import json
import zipfile
from osgeo import gdal
import rasterio
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import subprocess
from django.utils import timezone

SEQ_COLOR_DEFAULT = [
	(255, 0, 0, 255),
	(255, 128, 0, 255),
	(128, 255, 0, 255),
	(0, 255, 0, 255),
	(0, 255, 128, 255),
	(0, 255, 255, 255),
	(0, 128, 255, 255),
	(0, 0, 255, 255),
	(127, 0, 255, 255),
	(255, 0, 255, 255),
	(255, 0, 127, 255)
]

SEQ_GREY_SCALE_17 = [
	(15, 15, 15, 255),
	(30, 30, 30, 255),
	(45, 45, 45, 255),
	(60, 60, 60, 255),
	(75, 75, 75, 255),
	(90, 90, 90, 255),
	(105, 105, 105, 255),
	(120, 120, 120, 255),
	(135, 135, 135, 255),
	(150, 150, 150, 255),
	(165, 165, 165, 255),
	(180, 180, 180, 255),
	(195, 195, 195, 255),
	(210, 210, 210, 255),
	(225, 225, 225, 255),
	(240, 240, 240, 255),
	(255, 255, 255, 255)
]

def gerarPolygono(points, path, name):
	#coords = '['
	#for p in points:
	#	print(p)
	#	if coords != '[':
	#		coords = coords + ','
	#	coords = coords + '[' +str(p['lat'])+','+str(p['long'])+']'
	#coords = coords + ']' 
	polygono = {
		  "type": "FeatureCollection",
		  "features": [
		    {
		      "type": "Feature",
		      "properties": {},
		      "geometry": {
		        "type": "Polygon",
		        "coordinates": [
		          json.loads(points)
		        ]
		      }
		    }
		  ]
		}
	with open(path+name+'.geojson', 'w') as outfile:
		json.dump(polygono, outfile)
	return polygono

def unzip(request, ar):
	projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
	with zipfile.ZipFile('projetos/'+projeto.pasta+'/'+ar,"r") as zip_ref:
		zip_ref.extractall('projetos/'+projeto.pasta+'/')
	return redirect('/projeto/'+str(projeto.pk)+'/')

def convertToWGS84(src):
#### Conversion from UTM to WGS84 CRS 
	src_crs = src.crs['init'].upper()
	min_lon, min_lat, max_lon, max_lat = src.bounds
	bounds_orig = [[min_lat, min_lon], [max_lat, max_lon]]
	bounds_fin = []
	for item in bounds_orig:   
	    lat = item[0]
	    lon = item[1]
	    proj = Transformer.from_crs(int(src_crs.split(":")[1]), int(4326), always_xy=True)
	    lon_n, lat_n = proj.transform(lon, lat)
	    bounds_fin.append([lat_n, lon_n])
	centre_lon = bounds_fin[0][1] + (bounds_fin[1][1] - bounds_fin[0][1])/2
	centre_lat = bounds_fin[0][0] + (bounds_fin[1][0] - bounds_fin[0][0])/2
	
	return [bounds_fin, centre_lon, centre_lat]

def list_repositorios(stack_marked = '', tile = None):
	print(stack_marked)
	pathRepositorio = os.getcwd()+'/repositorio/sentinel'
	repos = []
	for item in os.listdir(pathRepositorio):
		if os.path.isfile(item):
			continue
		else:
			repo = RepoSentinel()
			repo.level = item[8:10]
			repo.data = item[11:19]
			repo.data_format = item[11:15] + '-'+item[15:17]+'-'+item[17:19]
			repo.sat = item[1:3]
			repo.tile = item[39:44]
			if stack_marked == repo.sat+repo.level+repo.data:
				repo.marked = True
			if tile==None:
				repos.append(repo)
			else:
				if repo.tile == tile:
					repos.append(repo)

	return repos

def list_filesinfolder(path):
	files = []
	for item in os.listdir(path):
		files.append(item)
	return files
def createOutputImageGDAL(outFilename, inDataset):
    driver = gdal.GetDriverByName( "GTiff" )
    metadata = driver.GetMetadata()
    if gdal.DCAP_CREATE in metadata and metadata[gdal.DCAP_CREATE] == 'YES':
        print('Driver GTiff supports Create() method.')
    else:
        print('Driver GTIFF does not support Create()')
        sys.exit(-1)
    geoTransform = inDataset.GetGeoTransform()
    geoProjection = inDataset.GetProjection()
    newDataset = driver.Create(outFilename, inDataset.RasterXSize,
    inDataset.RasterYSize, 1, gdal.GDT_Float32)
    newDataset.SetGeoTransform(geoTransform)
    newDataset.SetProjection(geoProjection)
    return newDataset

def reamostrar(raster, escala):
	data = raster.read(out_shape=(raster.count,int(raster.height * escala),int(raster.width * escala)),resampling=Resampling.bilinear)
	return data

def reamostrar_w(input, output, width, height):
	raster = rasterio.open(input)
	data = raster.read(out_shape=(raster.count, width, height),resampling=Resampling.bilinear)
	band_geo = raster.profile
	raster.close()
	band_geo.update({"width": width, "height": height})
	with rasterio.open(output, 'w', **band_geo) as dest:
		dest.write(data)


def montar_kwargs_gdal(path, name, dst = 'EPSG:32722', src = 'EPSG:32722'):
	kwargs = {'format': 'GTiff',
			  'geoloc': False,
			  'cutlineDSName': path + name + '.geojson',
			  'dstSRS': dst,
			  'srcSRS': src,
			  'cropToCutline': True,
			  'cutlineBlend': 10,
			  }
	return kwargs

def extremidades_mascara(path):
	with open(path) as data_file:
		geoms = json.loads(data_file.read())
	obj = geoms['features'][0]['geometry']
	locs = obj['coordinates'][0]
	max_lat = -99999999
	min_lat = 9999999
	max_long = -99999999
	min_long = 99999999
	for loc in locs:
		if loc[1] > max_lat:
			max_lat = loc[1]
		if loc[1] < min_lat:
			min_lat = loc[1]
		if loc[0] > max_long:
			max_long = loc[0]
		if loc[0] < min_long:
			min_long = loc[0]
	return max_lat, min_lat, max_long, min_long
def cortar_tif(path_mask, idmask, input, output, xRes=10, yRes=10):
	kwargs = montar_kwargs_gdal(path_mask, idmask)
	input = input
	out =  output
	ds = gdal.Warp(srcDSOrSrcDSTab = input,
         destNameOrDestDS=out,
		 **kwargs, xRes=xRes, yRes=yRes)

def exportRGBAClasse(path, file, colors):
	im = Image.open(os.path.join(path, file+'.tif'))
	im.thumbnail(im.size)
	wid, hgt = im.size
	im2 = rasterio.open(path + file + '.tif').read()
	#descobrir valores máximo e mínimo
	image = Image.new("RGBA", (wid, hgt), (255,255,255,0))
	for x in range(0, wid):
		for y in range(0, hgt):
			p = im2[0, y-1, x-1]
			if p == 0:
				color = (0, 0, 0, 0)
			else:
				try:
					color = (colors.loc[p,'r'], colors.loc[p,'g'], colors.loc[p,'b'],255)
				except:
					print("Erro"+str(p))
					color = (0, 0, 0, 0)

			image.putpixel((x, y), color)
	outfile = os.path.join(path, file +".png")
	image.save(outfile, "PNG", quality=100)

def hex_to_rgb(hex_string):
    str_len = len(hex_string)
    if hex_string.startswith("#"):
        if str_len == 7:
            r_hex = hex_string[1:3]
            g_hex = hex_string[3:5]
            b_hex = hex_string[5:7]
        elif str_len == 4:
            r_hex = hex_string[1:2] * 2
            g_hex = hex_string[2:3] * 2
            b_hex = hex_string[3:4] * 2
    elif str_len == 3:
        r_hex = hex_string[0:1] * 2
        g_hex = hex_string[1:2] * 2
        b_hex = hex_string[2:3] * 2
    else:
        r_hex = hex_string[0:2]
        g_hex = hex_string[2:4]
        b_hex = hex_string[4:6]
    return int(r_hex, 16), int(g_hex, 16), int(b_hex, 16)

def exportRGBA(path, file, min, max, div=4, seq=SEQ_COLOR_DEFAULT, gradiente=False):
	im = Image.open(os.path.join(path, file+'.tif'))
	im.thumbnail(im.size)
	wid, hgt = im.size
	#descobrir valores máximo e mínimo
	if (math.isnan(min)):
		max=0
		min=0
		for x in range(0, wid):
			for y in range(0, hgt):
				cordinate = x, y
				p = im.getpixel(cordinate)
				if (p>max):
					max = p
				if (p<min):
					min = p
	min = min + 0.00000001
	gradiente = paleta_fixa(min, max, div, seq, gradiente)
	image = Image.new("RGBA", (wid, hgt), (255,255,255,0))
	for x in range(0, wid):
		for y in range(0, hgt):
			cordinate = x, y
			p = im.getpixel(cordinate)
			color = (0, 0, 0, 0)
			for i in gradiente:
				if (p >= i.min) and (p <= i.max):
					color = i.cor
			image.putpixel((x, y), color)
	outfile = os.path.join(path, file +".png")
	image.save(outfile, "PNG", quality=100)

class Intervalo(object):
	id = 1
	min = 0.0
	max = 0.0
	cor = (0,0,0,0)

	def __init__(self, id, min, max, cor): 
		self.id = id
		self.min = min
		self.max = max
		self.cor = cor

	def __str__(self):
		return self.min + ' - ' + self.max

def paleta_fixa(min, max, div=4, seq=SEQ_COLOR_DEFAULT, gradiente=False):
	intervalo = (float(max) - float(min))/div
	gradiente = []
	i = 1
	while i<=div:
		gradiente.append(
			Intervalo(i, 
				min+intervalo*(i-1), 
				min+intervalo*(i),
				seq[i])
			)
		i=i+1
	return gradiente

def path_repositorio(level, data):
	path_input = ''
	for item in os.listdir(os.getcwd()+'/repositorio/sentinel/'):
		if os.path.isfile(item):
			continue
		else:
			if (level == item[8:10]):
				if (data == item[11:19]):
					path_input = os.getcwd()+'/repositorio/sentinel/'+item
	return path_input

def verificar_tile_mask(path_mask):
	api = SentinelAPI('juanmorysson', 'Blow642Sock095#', 'https://scihub.copernicus.eu/dhus')
	footprint = geojson_to_wkt(read_geojson(path_mask))
	products = api.query(footprint,
						 platformname='Sentinel-2',
						 producttype='S2MSI2A',
						 date=('20221106', '20221112'))
	products_df = api.to_dataframe(products)
	prds = products_df.loc[:,"title"]
	tiles = []
	for p in prds:
		tile = p[39:44]
		if tiles.__contains__(tile):
			print("")
		else:
			tiles.append(tile)
	return tiles

def verificaBool(b, v, f):
	if b:
		return v
	else:
		return f


def criar_barra(user, processo):
	bp = BarraProgresso()
	bp.percent = "0"
	bp.processo = processo
	bp.mov = "Iniciando..."
	bp.usuario = user
	bp.data_criacao = timezone.now()
	bp.save()
	return bp

def criar_banda(sensor, i, user):
	b = Raster()
	b.tag = "Band"+str(i)
	b.tagOnSat = "Band"+str(i)
	b.band = "Band"+str(i)
	b.satelite = sensor
	b.responsavel = user
	b.save()

def processoativo(progresso):
	bp = BarraProgresso.objects.get(pk=progresso.pk)
	return bp.ativo

def corClasse(geo):
	#area = AreaModelo.objects.get(pk=pk)
	#return area.classe.cor
	return geo['properties']['cor']