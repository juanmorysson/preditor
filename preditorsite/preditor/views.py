from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .class_utils import *
from .models import Projeto, BarraProgresso, Area, Modelo, ClasseModelo, AreaModelo, Raster_Modelo, Raster, Satelite
from .forms import ProjetoForm, AreaForm, ModeloForm, ClasseModeloForm, AreaModeloForm
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import HttpResponse,JsonResponse
from django.core.files.storage import default_storage
import zipfile
import glob
from . import calc, utils, progress, ia
from area import area as c_area
import csv

#import ee
from shapely.geometry import Polygon
from oauth2client import crypt
from django.views.generic import TemplateView
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt 
from skimage import data
from PIL import Image
import math
import rasterio
import folium
import json
import requests
from folium import plugins
from folium.plugins import Draw
from pyproj import Transformer
import sys, os, struct
from rasterio.io import MemoryFile
from skimage import exposure
from rasterio.plot import show
from datetime import datetime
from rasterio.plot import show_hist
from collections import OrderedDict
from sentinelsat import SentinelAPI
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
# Create your views here.

##########   PAGES   ##############
def index(request):
	#ia.ler_modelo()
	caldas_novas = f"media/cn.geojson"
	m = folium.Map(
		location=[-17.7494, -48.6202],
		tiles="cartodbpositron",
		zoom_start=10,
	)
	folium.GeoJson(caldas_novas, name="CN").add_to(m)
	folium.LayerControl().add_to(m)
	m=m._repr_html_()

	return render(request, 'preditor/index.html', {'my_map': m})
def modelos(request):
    #if not request.user.has_perm('aSocial.list_setor'):
    #    raise PermissionDenied
    modelos = Modelo.objects.all()
    return render(request, 'preditor/modelos.html', {'modelos': modelos })

def modelo_open(request, pk):
    #if not request.user.has_perm('aSocial.delete_setor'):
    #    raise PermissionDenied
	error = request.session.get('error')
	if error == None:
		error = ''
	else:
		del request.session['error']
	modelo = get_object_or_404(Modelo, pk=pk)
	path = os.getcwd()+'\\arquivos\\modelos\\'+modelo.pasta
	classes = ClasseModelo.objects.filter(modelo=modelo)
	rasters = Raster.objects.all()
	vars = []
	for r in rasters:
		rm = Raster_Modelo.objects.filter(modelo=modelo, raster=r)
		marked = False
		if len(rm)>0:
			marked = True
		v = Variavel(r.pk, r.tag, marked)
		vars.append(v)
	areas = []
	for classe in classes:
		areas2 = AreaModelo.objects.filter(classe=classe)
		if areas2:
			for area in areas2:
				areas.append(area)
	repos = utils.list_repositorios(modelo.stack)
	return render(request, 'preditor/modelo_open.html', {'modelo':modelo, 'error':error, 'classes':classes, 'vars': vars, 'areas':areas, 'repos':repos})

def gerar_stacks_modelo (request, pk):
	stack = ""
	vars = []
	rasters = []
	modelo = Modelo.objects.get(pk=pk)
	rms = Raster_Modelo.objects.filter(modelo=modelo)
	for rm in rms:
		Raster_Modelo.delete(rm)
	for k, v in request.POST.lists():
		if k.startswith('repo_'):
			stack = k[-12:]
			modelo.stack = stack
			modelo.save()
		if k.startswith('var_'):
			idRaster = k[4:len(k)]
			r = Raster.objects.get(pk=idRaster)
			rm = Raster_Modelo()
			rm.modelo = modelo
			rm.raster = r
			rm.save()
			vars.append(idRaster)
			rasters.append(r)
	cortarModelo(pk, stack, rasters)
	return redirect('modelo_open', pk=pk)

def ver_stacks_modelo (request, pk):
	modelo = Modelo.objects.get(pk=pk)
	stack = modelo.stack
	classes = ClasseModelo.objects.filter(modelo=modelo)
	areas = AreaModelo.objects.filter(classe__in=classes)
	list = []
	for area in areas:
		arqs = []
		for dirpath, dirnames, filenames in os.walk(os.getcwd() + '/arquivos/modelos/'+modelo.pasta+'/masks/'):
			for file in filenames:
				if file[:-8] == str(area.pk):
					arqs.append(Arquivo(file, 'Mascara'))
		for dirpath, dirnames, filenames in os.walk(os.getcwd() + '/arquivos/modelos/'+modelo.pasta+'/'+str(area.pk)+'/'):
			for file in filenames:
				tipo = "Indice"
				if file[-4:] == '.png':
					continue
				else:
					if dirpath[-7:]=="indices":
						tipo = file[:-4]
					if dirpath[-6:]=="cortes":
						tipo = "Cortes_"+file[:-4]
					else:
						if file=="declividade.tif":
							tipo="Declividade"
						if file=="altitude.tif":
							tipo="Altitude"
					arqs.append(Arquivo(file, tipo))
		areaList = AreaList(area.pk, area.descricao, arqs)
		list.append(areaList)
	return render(request, 'preditor/modelo_stacks.html', {'modelo':modelo, 'list':list})

def modelo_new(request):
    #if not request.user.has_perm('aSocial.add_setor'):
    #    raise PermissionDenied
    if request.method == "POST":
        form = ModeloForm(request.POST)
        if form.is_valid():
            modelo = form.save(commit=False)
            modelo.responsavel = request.user
            modelo.data_criacao = timezone.now()
            pasta=request.POST['pasta'].replace(" ", "")
            modelo.pasta = pasta 
            os.mkdir('arquivos/modelos/'+pasta)
            os.mkdir('arquivos/modelos/'+pasta+'/temp')
            os.mkdir('arquivos/modelos/'+pasta+'/masks')
            modelo.save()
            return redirect('modelo_open', pk=modelo.pk)
    else:
        form = ModeloForm()
    return render(request, 'preditor/modelo_edit.html', {'form': form})

def modelo_edit(request, pk):
    #if not request.user.has_perm('aSocial.add_setor'):
    #    raise PermissionDenied
    modelo = Modelo.objects.get(pk=pk)
    pasta_old = modelo.pasta
    if request.method == "POST":
        form = ModeloForm(request.POST, instance=modelo)
        if form.is_valid():
            modelo = form.save(commit=False)
            pasta=request.POST['pasta'].replace(" ", "")
            modelo.pasta = pasta
            os.rename(
            	os.path.join('arquivos/modelos/', pasta_old),
            	os.path.join('arquivos/modelos/', pasta)) 
            modelo.save()
            return redirect('modelo_open', pk=modelo.pk)
    else:
        form = ModeloForm(instance=modelo)
    return render(request, 'preditor/modelo_edit.html', {'form': form})


def classe_modelo_new(request, pk):
    #if not request.user.has_perm('aSocial.add_setor'):
    #    raise PermissionDenied
    modelo = get_object_or_404(Modelo, pk=pk)
    if request.method == "POST":
        form = ClasseModeloForm(request.POST)
        if form.is_valid():
            classe = form.save(commit=False)
            classe.modelo = modelo
            classe.save()
            return redirect('modelo_open', pk=modelo.pk)
    else:
        form = ClasseModeloForm()
    return render(request, 'preditor/classe_modelo_edit.html', {'form': form, 'modelo':modelo})

def classe_modelo_edit(request, pk):
#    if not request.user.has_perm('aSocial.change_curso'):
#        raise PermissionDenied
    classe = get_object_or_404(ClasseModelo, pk=pk)
    modelo = classe.modelo
    if(request.method == "POST"):
        form = ClasseModeloForm(request.POST, instance=classe)
        if form.is_valid():
            classe = form.save(commit=False)
            classe.modelo = modelo
            classe.save()           
            return redirect('modelo_open', pk=classe.modelo.pk)
    else:
        form = ClasseModeloForm(instance=classe)
    return render(request, 'preditor/classe_modelo_edit.html', {'form': form, 'modelo':classe.modelo})

def area_modelo_new(request, pk):
    #if not request.user.has_perm('aSocial.add_setor'):
    #    raise PermissionDenied
    modelo = get_object_or_404(Modelo, pk=pk)
    if request.method == "POST":
        form = AreaModeloForm(pk, request.POST)
        if form.is_valid():
            area = form.save(commit=False)
            classe = form.cleaned_data.get('Classe')
            area.classe = classe
            area.save()
            return redirect('area_modelo_edit', pk=area.pk)
    else:
        form = AreaModeloForm(pk)
    return render(request, 'preditor/area_modelo_edit.html', {'form': form, 'modelo':modelo})

def area_modelo_edit(request, pk):
#    if not request.user.has_perm('aSocial.change_curso'):
#        raise PermissionDenied
    area = get_object_or_404(AreaModelo, pk=pk)
    classe = area.classe
    error = request.session.get('error')
    if error == None:
    	error = ''
    else:
    	del request.session['error']
    path = os.getcwd()+'\\arquivos\\modelos\\'+area.classe.modelo.pasta+'\\masks\\'
    mask = path+str(area.pk)+".geojson"
    m = None
    if(request.method == "POST"):
        form = AreaModeloForm(area.classe.modelo.pk, request.POST, instance=area)
        if os.path.isfile(mask):
        	if form.is_valid():
        		area = form.save(commit=False)
        		classe = form.cleaned_data.get('Classe')
        		area.classe = classe
        		area.save()           
        		return redirect('modelo_open', pk=area.classe.modelo.pk)
        else:
        	error = 'É obrigatório ter uma área demarcada'
    else:
        form = AreaModeloForm(area.classe.modelo.pk, instance=area, initial={'Classe': classe})
        if os.path.isfile(mask):
        	with open(mask) as data_file:
        		geoms= json.loads(data_file.read())
        	obj = geoms['features'][0]['geometry']
        	area_m = c_area(obj)
        	m = folium.Map(
        		location=[-17.7494, -48.6202],
        		tiles="cartodbpositron",
        		zoom_start=10,
        		)
        	folium.GeoJson(mask, name=area.descricao).add_to(m)
        	folium.LayerControl().add_to(m)
        	m=m._repr_html_()

    return render(request, 'preditor/area_modelo_edit.html', {'form': form, 'modelo':area.classe.modelo, 'area':area, 'my_map': m, 'error':error})

def projetos(request):
    #if not request.user.has_perm('aSocial.list_setor'):
    #    raise PermissionDenied
    projetos = Projeto.objects.all()
    return render(request, 'preditor/projetos.html', {'projetos': projetos, 
    	#'per_edit_setor': request.user.has_perm('aSocial.change_setor'),
    	#'per_delete_setor':request.user.has_perm('aSocial.delete_setor'),
    	#'per_add_setor':request.user.has_perm('aSocial.add_setor')
    	})

def projeto_open(request, pk):
    #if not request.user.has_perm('aSocial.delete_setor'):
    #    raise PermissionDenied
    error = request.session.get('error')
    if error == None:
    	error = ''
    else:
    	del request.session['error']
    projeto = get_object_or_404(Projeto, pk=pk)
    areas = Area.objects.filter(projeto=projeto)
    path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta
    l2 = len(path)
    shapes = []
    for dirpath, dirnames, filenames in os.walk(path):
    	for file in filenames:
    		dir = ""
    		if (l2-len(dirpath))<0:
    			dir = dirpath[l2-len(dirpath):]
    		arquivo = Arquivo("","")
    		arquivo.desc = file
    		if (len(file) > 8):
    			arquivo.tipo = file[-9]
    			if (file[-8:] ==".geojson"):
    				shapes.append(arquivo)
    request.session['projeto_pk'] = pk
    request.session['projeto_desc'] = projeto.descricao
    request.session.modified = True
    return render(request, 'preditor/projeto_open.html', {'projeto':projeto, 'areas':areas, 'shapes':shapes, 'error':error})

def area_open(request, pk):
    #if not request.user.has_perm('aSocial.delete_setor'):
    #    raise PermissionDenied
    area = Area.objects.get(pk=pk)
    projeto = Projeto.objects.get(pk=area.projeto.pk)
    path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta
    mask = path+"\\mask\\"+str(area.pk)+".geojson"
    #calculando área m2
    if os.path.isfile(mask):
    	print("mask ok")
    else:
    	return redirect('projeto_open', pk=projeto.pk)
    with open(mask) as data_file:
    	geoms= json.loads(data_file.read())
    obj = geoms['features'][0]['geometry']
    area_m = c_area(obj)
    ####mapa
    m = folium.Map(
    	location=[-17.7494, -48.6202],
    	tiles="cartodbpositron",
    	zoom_start=10,
    )
    folium.GeoJson(mask, name=area.descricao).add_to(m)
    folium.LayerControl().add_to(m)
    m=m._repr_html_()
    dec = glob.glob(path+'/declividade.tif')
    alt = glob.glob(path+'/altitude.tif')
    repos = utils.list_repositorios()
    return render(request, 'preditor/area_open.html', {'projeto':projeto, 'area':area, 'my_map': m, 'dec':dec, 'alt':alt, 'repos':repos, 'area_m':area_m})

def stack(request, pk, stack):
    #if not request.user.has_perm('aSocial.delete_setor'):
    #    raise PermissionDenied
    request.session['hash_progress'] = hash("ndvi"+str(timezone.now()))
    area = Area.objects.get(pk=pk)
    projeto = Projeto.objects.get(pk=area.projeto.pk)
    repo = RepoSentinel()
    repo.level = stack[2:4]
    repo.data = stack[4:13]
    repo.sat = stack[0:2]
    path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\'+stack
    l = len(path+'\\cortes')
    cortes = []
    for dirpath, dirnames, filenames in os.walk(path+'\\cortes'):
    	for file in filenames:
    		arquivo = Arquivo("","")
    		arquivo.tipo = file[-3:]
#    		dir = ""
#    		if (l-len(dirpath))<0:
#    			dir = dirpath[l-len(dirpath):]
    		if (arquivo.tipo == "tif"):
    			arquivo.desc = file[:-4]
    			cortes.append(arquivo)
    indices = []
    if len(cortes) > 0:
    	l = len(path+'\\indices')
    	for dirpath, dirnames, filenames in os.walk(path+'\\indices'):
    		for file in filenames:
    			arquivo = Arquivo("","")
    			arquivo.tipo = file[-3:]
    			if (arquivo.tipo == "tif"):
    				arquivo.desc = file
    				indices.append(arquivo)
#    			dir = ""
#    			if (l-len(dirpath))<0:
#    				dir = dirpath[l-len(dirpath):]
#    			arquivo.desc = '{}/{}'.format(dir, file)
#    			indices.append(arquivo)
    return render(request, 'preditor/stack.html', {'projeto':projeto, 'area':area, 'indices':indices, 'cortes': cortes, 'repo':repo })


def projeto_new(request):
    #if not request.user.has_perm('aSocial.add_setor'):
    #    raise PermissionDenied
    if request.method == "POST":
        form = ProjetoForm(request.POST)
        if form.is_valid():
            projeto = form.save(commit=False)
            projeto.responsavel = request.user
            projeto.data_criacao = timezone.now()
            pasta=request.POST['pasta'].replace(" ", "")
            projeto.pasta = pasta 
            os.mkdir('arquivos/projetos/'+pasta)
            os.mkdir('arquivos/projetos/'+pasta+'/temp')
            projeto.save()
            return redirect('projeto_open', pk=projeto.pk)
    else:
        form = ProjetoForm()
    return render(request, 'preditor/projeto_edit.html', {'form': form})

def area_new(request):
    #if not request.user.has_perm('aSocial.add_setor'):
    #    raise PermissionDenied
    projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
    if request.method == "POST":
        form = AreaForm(request.POST)
        if form.is_valid():
            area = form.save(commit=False)
            area.responsavel = request.user
            area.data_criacao = timezone.now()
            area.projeto = projeto
            pasta=request.POST['pasta'].replace(" ", "") 
            area.pasta = pasta
            os.mkdir('arquivos/projetos/'+projeto.pasta+'/'+pasta)
            os.mkdir('arquivos/projetos/'+projeto.pasta+'/'+pasta+'/temp')
            os.mkdir('arquivos/projetos/'+projeto.pasta+'/'+pasta+'/mask')
            area.save()
            return redirect('/projeto/'+str(projeto.pk)+"/")
    else:
        form = AreaForm()
    return render(request, 'preditor/area_edit.html', {'form': form, 'projeto': projeto})

def draw(request):
	projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
	m = folium.Map(
		location=[-17.7494, -48.6202],
		tiles="cartodbpositron",
		zoom_start=10,
	)
	draw = Draw(
		export=True, 
		draw_options={'polygon':{'showArea':True}}, 
		edit_options= {
			'selectedPathOptions':{
				'maintainColor': True,
				'opacity': 0.3}
				},
		filename='projetos'+projeto.pasta+'shape.geojson')
	draw.add_to(m)
	m=m._repr_html_()

	return render(request, 'preditor/draw.html', {'my_map': m})

def download_page(request):
	files = glob.glob(os.getcwd()+'/repositorio/sentinel/*/GRANULE/*/IMG_DATA/*.jp2')
	return render(request, 'preditor/download_page.html', {'files':files})

def trescores_page(request):
	return render(request, 'preditor/trescores_page.html', {})

def progressos(request):
	progressos = BarraProgresso.objects.filter(data_finalizacao__isnull=True).order_by('-data_criacao')
	return render(request, 'preditor/progressos.html', {'progressos' : progressos})

def ndvi_page(request):
	request.session['hash_progress'] = hash("ndvi"+str(timezone.now()))
	return render(request, 'preditor/ndvi_page.html', {})

def cortar_page(request):
	projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
	rasters = glob.glob(os.getcwd()+'/repositorio/sentinel/*/GRANULE/*/IMG_DATA/*.jp2')
	masks = glob.glob(os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\*.geojson')
	return render(request, 'preditor/cortar.html', {'rasters':rasters, 'masks':masks})

def user(request):
    return render(request, 'aSocial/user.html', {})






##########   ACTIONS BUTTONS  ##############
def clear_projeto_sessao(request):
    #if not request.user.has_perm('aSocial.delete_setor'):
    #    raise PermissionDenied
    del request.session['projeto_pk']
    del request.session['projeto_desc']
    return redirect('/projetos')

def uploadMask(request, pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	if (request.FILES.get('mask_'+str(pk), False)==False):
		request.session['error']='Adicione um arquivo Geojson!'
		return redirect('/projeto/'+str(projeto.pk))
	mask = request.FILES['mask_'+str(pk)]
	if (mask.name[-8:]!='.geojson'):
		request.session['error']='Adicione um arquivo Geojson!'
		return redirect('/projeto/'+str(projeto.pk))
	path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\mask\\'
	with default_storage.open(path+str(pk)+'.geojson', 'wb+') as destination:
		for chunk in mask.chunks():
			destination.write(chunk)
	return redirect('/projeto/'+str(projeto.pk))

def uploadPoints(request, pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	if (request.FILES.get('mask_'+str(pk), False)==False):
		request.session['error']='Adicione um arquivo .csv!'
		return redirect('/projeto/'+str(projeto.pk))
	arquivo = request.FILES['mask_'+str(pk)]
	if (arquivo.name[-4:]!='.csv'):
		request.session['error']='Adicione um arquivo .csv!'
		return redirect('/projeto/'+str(projeto.pk))
	path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\mask\\'
	with default_storage.open(path+str(pk)+'.csv', 'wb+') as destination:
		for chunk in arquivo.chunks():
			destination.write(chunk)
	arq = open(path+str(pk)+'.csv')
	reader = csv.reader(arq)
	points = []
	for linha in reader:
		if linha != ['lat;long']:
			points.append(linha)
		p = str(points)
		p = p.replace("'", "")
		p = p.replace(";", ",")
	utils.gerarPolygono(p, path, str(pk))
	return redirect('/projeto/'+str(projeto.pk))

def uploadMaskModelo(request, pk):
	area = AreaModelo.objects.get(pk=pk)
	modelo = area.classe.modelo
	if (request.FILES.get('mask_'+str(pk), False)==False):
		request.session['error']='Adicione um arquivo Geojson!'
		return redirect('/area_modelo/'+str(area.pk))
	mask = request.FILES['mask_'+str(pk)]
	if (mask.name[-8:]!='.geojson'):
		request.session['error']='Adicione um arquivo Geojson!'
		return redirect('/area_modelo/'+str(area.pk))
	path = os.getcwd()+'\\arquivos\\modelos\\'+modelo.pasta+'\\masks\\'
	with default_storage.open(path+str(pk)+'.geojson', 'wb+') as destination:
		for chunk in mask.chunks():
			destination.write(chunk)
	return redirect('/area_modelo/'+str(area.pk))

def uploadPointsModelo(request, pk):
	area = AreaModelo.objects.get(pk=pk)
	modelo = area.classe.modelo
	if (request.FILES.get('mask_'+str(pk), False)==False):
		request.session['error']='Adicione um arquivo .csv!'
		return redirect('/area_modelo/'+str(area.pk))
	arquivo = request.FILES['mask_'+str(pk)]
	if (arquivo.name[-4:]!='.csv'):
		request.session['error']='Adicione um arquivo .csv!'
		return redirect('/area_modelo/'+str(area.pk))
	path = os.getcwd()+'\\arquivos\\modelos\\'+modelo.pasta+'\\masks\\'
	with default_storage.open(path+str(pk)+'.csv', 'wb+') as destination:
		for chunk in arquivo.chunks():
			destination.write(chunk)
	arq = open(path+str(pk)+'.csv')
	reader = csv.reader(arq)
	points = []
	for linha in reader:
		if linha != ['lat;long']:
			points.append(linha)
		p = str(points)
		p = p.replace("'", "")
		p = p.replace(";", ",")
	utils.gerarPolygono(p, path, str(pk))
	return redirect('/area_modelo/'+str(area.pk))

def trescores(request):
	nome = request.POST['nome']
	print(timezone.now())
	print("lendo arquivos...")
	file_red = MemoryFile(request.FILES['red'])
	band2 = file_red.open()
	file_green = MemoryFile(request.FILES['green'])
	band3 = file_green.open()
	file_blue = MemoryFile(request.FILES['blue'])
	band4 = file_blue.open()
	#band2=rasterio.open("sentinel/T22KGF_20211203T133221_B02.jp2")
	#band3=rasterio.open("sentinel/T22KGF_20211203T133221_B03.jp2")
	#band4=rasterio.open("sentinel/T22KGF_20211203T133221_B04.jp2")

	projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
	
	######## criando rgb.tiff	
	band2_geo = band2.profile
	band2_geo.update({"count": 3})
	
	print("criando rgb.tiff...")
	with rasterio.open('projetos/'+projeto.pasta+'/'+nome+'.tiff', 'w', **band2_geo) as dest:
		dest.write(band2.read(1),1)
		dest.write(band3.read(1),2)
		dest.write(band4.read(1),3)
	

	
	#### abrindo imagem
	src = rasterio.open('projetos/'+projeto.pasta+'/'+nome+'.tiff')
	imgRio = src.read()

	location = utils.convertToWGS84(src)
	

	####Visualização no folium
	print("Visualização no folium...")
	m = folium.Map(
		location=[location[2], location[1]], 
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=9
	)

	
	####Redução de Raster
	print(timezone.now())
	print("reduzindo raster...")
	utils.reduzir_raster('projetos/'+projeto.pasta+'/'+nome+'.tiff',
		'projetos/'+projeto.pasta+'/'+nome+'_reduzida.tiff')
	

	src = rasterio.open('projetos/'+projeto.pasta+'/'+nome+'_reduzida.tiff')
	imgRed = src.read()

	print(timezone.now())
	print("convertendo png...")
	utils.exportRGBA('projetos/'+projeto.pasta+'/temp/', 'plot', imgRed.min, imgRed.max)

	#add imagem do disco
	merc = os.path.join("projetos/"+projeto.pasta+"/temp", "plot.png")
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		print("adicionado imagem...")
		imgR = folium.raster_layers.ImageOverlay(
			name="Imagem PNG",
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		#folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)
	

	####to html	
	print(timezone.now())
	print("to html...")
	m=m._repr_html_()

	return render(request, 'preditor/trescores_page.html', {'my_map': m})

def histograma(request):
	img = rasterio.open('media/rgb.tiff')
	fig, ax = plt.subplots(1,figsize=(7,7))
	#show(img, ax=axrgb)
	#show(img, ax=axhist)
	
	show_hist(
		img, bins=10, masked=True, 
		title='Histogram', ax=None, label=None)
	plt.close()
	fig.savefig('media/histogram.png') 

	return render(request, 'preditor/rgb_page.html', {'file_url':"media/rgb.jpg", 'hist_url':"media/histogram.png", })

percent = 0.0

def cortar(request, pk, stack):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	id = str(area.pk)
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\'+stack
	corte(id, repo, path, path + '/../mask/')
	
	return redirect('stack', pk, stack)


def cortarModelo(pk, stack, rasters):
	modelo = Modelo.objects.get(pk=pk)
	classes = ClasseModelo.objects.filter(modelo=modelo)
	areas = AreaModelo.objects.filter(classe__in=classes)
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	for area in areas:
		id = str(area.pk)
		print("Iniciando área"+id)
		path_area = os.getcwd() + '\\arquivos\\modelos\\' + modelo.pasta + '\\' + id
		if os.path.isdir(path_area):
			print("path Já Criado")
		else:
			os.mkdir(path_area)
		path = os.getcwd() + '\\arquivos\\modelos\\' + modelo.pasta + '\\' + id + '\\' + stack
		corte(id, repo, path, path + '/../../masks/')
		for r in rasters:
			if r.isIndex:
				if r.tag == 'Declividade':
					print("Cortando Declividade")
					utils.cortar_tif(path_area + '/../masks/', id,
									 'repositorio/topodata/declividade_caldas.tif',
									 path_area+'/declividade.tif')
				if r.tag == 'Altitude':
					print("Cortando Altitude")
					utils.cortar_tif(path_area + '/../masks/', id,
									 'repositorio/topodata/altitude_caldas.tif',
									 path_area+'/altitude.tif')
				if (r.tag != 'Declividade' and r.tag != 'Altitude'):
					print("Gerando Índice" + r.tag)
					s = "Sentinel"+repo.level
					sats = Satelite.objects.filter(descricao=s)
					sat = None
					for s in sats:
						sat = s
					print(sat)
					src_ref = rasterio.open(path+'\\cortes\\'+sat.bandReferencia+'.tif')
					raster = calc.indice_calc_formula(src_ref, sat, r.formula, path)
					calc.indice_write_tif(raster, src_ref, path +'\\indices\\', r.tag)
		print("Finalizado ")
	return redirect('stack', pk, stack)
def corte(id, repo, path, path_mask):
	t_file_name = -11
	if (repo.level == '1C'):
		t_file_name = -7
	#### criar pastas
	if os.path.isdir(path):
		print("path Já Criado")
	else:
		os.mkdir(path)
		os.mkdir(path + '\\cortes')
		os.mkdir(path + '\\indices')
	#### Cortar com gdal
	# es_obj = {'a':...,'b':..., 'c':...}
	kwargs = utils.montar_kwargs_gdal(path_mask, id)
	path_input = ''
	path_input = utils.path_repositorio(repo.level, repo.data)
	l = len(path)
	rasters = []
	# gdal.SetConfigOption('GDAL_HTTP_UNSAFESSL', 'YES')
	for dirpath, dirnames, filenames in os.walk(path_input):
		for file in filenames:
			if (len(file) > 8):
				if (file[-4:] == '.jp2'):
					if (file[:3] != "MSK"):
						input = dirpath + '\\' + file
						out = path + '\\cortes\\' + file[t_file_name:-4] + '.tif'
						gdal.Warp(srcDSOrSrcDSTab=input,
								  destNameOrDestDS=out, **kwargs, xRes=10, yRes=10)

def progress_callback(complete, message, self):
	percent = math.floor(complete * 100)



def declividade_gerar(request, pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	path = 'arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	#### Cortar com gdal
	kwargs = utils.montar_kwargs_gdal(path+'/mask/', str(area.pk))
	input = 'repositorio/topodata/declividade_caldas.tif'
	out =  path+'/declividade.tif'
	ds = gdal.Warp(srcDSOrSrcDSTab = input,
         destNameOrDestDS=out,
		 **kwargs)

	src = rasterio.open(path+'/declividade.tif')
	src_saida = src.read()
	location = utils.convertToWGS84(src)
	###postar no mapa
	####Visualização no folium
	print("Visualização no folium...")
	m = folium.Map(
		location=[location[2], location[1]], 
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=12
	)
	utils.exportRGBA(path, "declividade", 0.0, src_saida.max(), 10)
	#add imagem do disco
	merc = os.path.join(path+'/', 'declividade.png')
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		imgR = folium.raster_layers.ImageOverlay(
			name="Declividade",
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)
	m=m._repr_html_()
	
	return render(request, 'preditor/mapa.html', {'my_map': m, 'area':area})

def declividade(request, pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	path = 'arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	src_saida = rasterio.open(path+'/declividade.tif')
	location = utils.convertToWGS84(src_saida)
	m = folium.Map(
		location=[location[2], location[1]], 
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=12
	)
	#add imagem do disco
	merc = os.path.join(path+'/', 'declividade.png')
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		imgR = folium.raster_layers.ImageOverlay(
			name="Declividade",
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)
	m=m._repr_html_()
	
	return render(request, 'preditor/mapa.html', {'my_map': m, 'area':area})

def altitude_gerar(request, pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	path = 'arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	#### Cortar com gdal
	kwargs = utils.montar_kwargs_gdal(path+'/mask/', str(area.pk))

	input = 'repositorio/topodata/altitude_caldas.tif'
	out =  path+'/altitude.tif'
	ds = gdal.Warp(srcDSOrSrcDSTab = input,
         destNameOrDestDS=out,
		 **kwargs)

	src = rasterio.open(path+'/altitude.tif')
	src_saida = src.read()
	location = utils.convertToWGS84(src)
	###postar no mapa
	####Visualização no folium
	print("Visualização no folium...")
	m = folium.Map(
		location=[location[2], location[1]], 
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=12
	)
	utils.exportRGBA(path, "altitude", 0.0, src_saida.max(), 10)
	#add imagem do disco
	merc = os.path.join(path+'/', 'altitude.png')
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		imgR = folium.raster_layers.ImageOverlay(
			name="Atltitude",
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)
	m=m._repr_html_()
	
	return render(request, 'preditor/mapa.html', {'my_map': m, 'area':area})

def altitude(request,pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	path = 'arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	src_saida = rasterio.open(path+'/altitude.tif')
	location = utils.convertToWGS84(src_saida)
	m = folium.Map(
		location=[location[2], location[1]], 
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=12
	)
	#add imagem do disco
	merc = os.path.join(path+'/', 'altitude.png')
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		imgR = folium.raster_layers.ImageOverlay(
			name="Atltitude",
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)
	m=m._repr_html_()
	
	return render(request, 'preditor/mapa.html', {'my_map': m, 'area':area})

def download_sentinel(request):
	projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
	data_ini = request.POST['data_ini']
	data_fim = request.POST['data_fim']
	
	data_ini = ''.join(filter(lambda i: i not in "-", data_ini))
	data_fim = ''.join(filter(lambda i: i not in "-", data_fim))
	
	api = SentinelAPI('juanmorysson', 'Blow642Sock095#', 'https://scihub.copernicus.eu/dhus')
	tiles = ['22KGF',]

	query_kwargs = {
        'platformname': 'Sentinel-2',
        'producttype': 'S2MSI1C',
        'date': (data_ini, data_fim)}
	'''
	https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
    Sentinel-1: SLC, GRD, OCN
    Sentinel-2: S2MSI2A,S2MSI1C, S2MS2Ap
    Sentinel-3: SR_1_SRA___, SR_1_SRA_A, SR_1_SRA_BS, SR_2_LAN___, OL_1_EFR___, OL_1_ERR___, OL_2_LFR___, OL_2_LRR___, SL_1_RBT___, SL_2_LST___, SY_2_SYN___, SY_2_V10___, SY_2_VG1___, SY_2_VGP___.
    Sentinel-5P: L1B_IR_SIR, L1B_IR_UVN, L1B_RA_BD1, L1B_RA_BD2, L1B_RA_BD3, L1B_RA_BD4, L1B_RA_BD5, L1B_RA_BD6, L1B_RA_BD7, L1B_RA_BD8, L2__AER_AI, L2__AER_LH, L2__CH4, L2__CLOUD_, L2__CO____, L2__HCHO__, L2__NO2___, L2__NP_BD3, L2__NP_BD6, L2__NP_BD7, L2__O3_TCL, L2__O3____, L2__SO2___. 
	'''
   
#'date': ('NOW-14DAYS', 'NOW')}

	print(data_ini)
	products = OrderedDict()
	for tile in tiles:
	    kw = query_kwargs.copy()
	    kw['tileid'] = tile
	    pp = api.query(**kw)
	    products.update(pp)

	#print(products)

	api.download_all(products, directory_path='repositorio/sentinel/')
	print("XXXXXXXXXXX Inciando unzip")
	#unzip downloads
	path = os.getcwd()+'\\repositorio\\sentinel\\'
	for dirpath, dirnames, filenames in os.walk(path):
		for file in filenames:
			if file[-3:]=="zip":
				with zipfile.ZipFile('{}/{}'.format(dirpath, file),"r") as zip_ref:
					zip_ref.extractall(dirpath)
				os.remove('{}/{}'.format(dirpath, file))
	return render(request, 'preditor/download_page.html', {'data_ini': data_ini})

def ndvi(request, pk, stack):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\'+stack
	progresso = progress.progress_create(projeto, "ndvi", request)
	if progresso:
		print(progresso.hash)
	progress.progress_save(5, "lendo arquivos...", progresso)
	nome = 'ndvi'
	print(timezone.now())
	print("lendo arquivos...")

	src_red = rasterio.open(path+'\\cortes\\B04.tif')
	src_nir = rasterio.open(path+'\\cortes\\B08.tif')
	####NDVI
	progress.progress_save(15, "Calculando NDVI - isso pode demorar...", progresso)
	ndvi = calc.ndvi(src_red, src_nir)

	progress.progress_save(60, "Escrevendo Imagem", progresso)
	calc.ndvi_write(ndvi, src_red, path+'\\indices\\', nome)

	progress.progress_save(100, "Concluído", progresso)

	return redirect('stack', pk, stack) 


def ndvi2(request, pk, stack):
	projeto = get_object_or_404(Projeto, pk=request.session.get('projeto_pk'))
	progresso = progress.progress_create(projeto, "ndvi", request)
	if progresso:
		print(progresso.hash)
	progress.progress_save(5, "lendo arquivos...", progresso)
	nome = request.POST['nome']
	print(timezone.now())
	print("lendo arquivos...")
	file_red = MemoryFile(request.FILES['red'])
	src_red = file_red.open()
	file_nir = MemoryFile(request.FILES['nir'])
	src_nir = file_nir.open()

	url = 'projetos/'+projeto.pasta+'/temp/'
	####NDVI
	progress.progress_save(15, "Calculando NDVI - isso pode demorar...", progresso)
	ndvi = calc.ndvi(src_red, src_nir)

	progress.progress_save(60, "Escrevendo Imagem", progresso)
	calc.ndvi_write(ndvi, src_red, url, nome)

	progress.progress_save(80, "Abrindo Imagem NDVI...", progresso)
	#### abrindo imagem
	src = rasterio.open(url+nome+'.tif')
	imgRio = src.read()

	progress.progress_save(83, "Corrigindo sistema de coordenadas...", progresso)
	location = utils.convertToWGS84(src)
	

	####Visualização no folium
	print("Visualização no folium...")
	m = folium.Map(
		location=[location[2], location[1]], 
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=9
	)

	progress.progress_save(89, "Convertendo PNG...", progresso)
	print(timezone.now())
	print("convertendo png...")
	utils.export_window(imgRio, 'projetos/'+projeto.pasta+'/temp/plotndvi.png')
	
	#add imagem do disco
	merc = os.path.join("projetos/"+projeto.pasta+"/temp", "plotndvi.png")
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		print("adicionado imagem...")
		imgR = folium.raster_layers.ImageOverlay(
			name="Imagem PNG",
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		#folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)

	progress.progress_save(100, "Concluído", progresso)
	####to html	
	print(timezone.now())
	print("to html...")
	m=m._repr_html_()
	return JsonResponse({'my_map': m}) 

def mapa_json(request, pk, stack, tipo, menu="Projeto"):
    #if not request.user.has_perm('aSocial.list_curso'):
        #raise PermissionDenied
    #### abrindo imagem
	path = ""
	file = ""
	div = 10
	paleta = utils.SEQ_COLOR_DEFAULT
	if menu=="Projeto":
		area = Area.objects.get(pk=pk)
		projeto = Projeto.objects.get(pk=area.projeto.pk)
		path = os.getcwd() + '\\arquivos\\projetos\\' + projeto.pasta + '\\' + area.pasta + '\\' + stack + '\\indices\\'
		if (tipo=="Declividade"):
			path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\'
			file = "declividade"
		if (tipo=="Altitude"):
			path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\'
			file = "altitude"
		if(tipo == "Mascara"):
			path = os.getcwd()+'\\arquivos\\projetos\\'+projeto.pasta+'\\'+area.pasta+'\\mask\\'
	if menu=="Modelo":
		area = AreaModelo.objects.get(pk=pk)
		modelo = Modelo.objects.get(pk=area.classe.modelo.pk)
		path_base = os.getcwd() + '\\arquivos\\modelos\\' + modelo.pasta
		path = os.getcwd() + '\\arquivos\\modelos\\' + modelo.pasta + '\\'+str(area.pk)+'\\'+stack+'\\indices\\'
		if (tipo == "Mascara"):
			path = path_base + '\\masks\\'
		if (tipo == "Declividade"):
			path = path_base + '\\'+str(area.pk)+'\\'
			file = "declividade"
		if (tipo == "Altitude"):
			path = path_base + '\\'+str(area.pk)+'\\'
			file = "altitude"
	if (tipo == "Mascara"):
		mask = path+str(area.pk)+".geojson"
		m = folium.Map(
			location=[-17.7494, -48.6202],
			tiles="cartodbpositron",
			zoom_start=10,
		)
		folium.GeoJson(mask, name="Máscara").add_to(m)
		folium.LayerControl().add_to(m)
		m=m._repr_html_()
	else:
		pasta = ""
		if(tipo[:7]=='Cortes_'):
			pasta = 'cortes/'
			tipo = tipo[7:]
			path = path[:-8]+pasta
			paleta = utils.SEQ_GREY_SCALE_17
			div = 16
		if file =="":
			file = tipo
		src = rasterio.open(path+file+'.tif')
		src_saida = src.read()
		location = utils.convertToWGS84(src)
		####Visualização no folium
		print("Visualização no folium...")
		m = folium.Map(
			location=[location[2], location[1]], 
			tiles='Stamen Terrain',
			#tiles="cartodbpositron",
			zoom_start=12
		)
		min_n = src_saida.min()
		if (tipo=="Declividade" or tipo=="Altitude"):
			min_n = 0.0
		utils.exportRGBA(path, file, min_n, src_saida.max(), div, paleta)
		#add imagem do disco
		merc = os.path.join(path, file+".png")
		if not os.path.isfile(merc):
			print(f"Could not find {merc}")
		else:
			imgR = folium.raster_layers.ImageOverlay(
				name=tipo,
				image=merc,
				bounds=location[0],
				opacity=1,
			)
			#folium.Popup("I am an image").add_to(imgR)
			imgR.add_to(m)
			folium.LayerControl().add_to(m)	
		m=m._repr_html_()

	return JsonResponse({'my_map_modal': m, 'tipo':tipo})

