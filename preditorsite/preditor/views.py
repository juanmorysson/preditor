import pandas as pd
import locale
from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from .class_utils import *
from .models import *
from .forms import *
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import HttpResponse,JsonResponse
from django.core.files.storage import default_storage
import zipfile
import glob
import joblib
from . import calc, utils, progress, ia
from area import area as c_area
import csv
import secrets
from sklearn.model_selection import train_test_split

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
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
# Create your views here.

##########   PAGES   ##############
def index(request):
	return render(request, 'preditor/index.html', {})
def mapa_cerrado(request):
	cerrado = f"media/cerrado.geojson"
	m = folium.Map(
		location=[-14.7494, -48.6202],
		tiles="cartodbpositron",
		zoom_start=5,
	)
	folium.GeoJson(cerrado, name="Cerrado").add_to(m)
	folium.LayerControl().add_to(m)
	m=m._repr_html_()

	return render(request, 'preditor/mapa_cerrado.html', {'my_map': m})
def modelos(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelos = Modelo.objects.filter(responsavel=request.user)
	return render(request, 'preditor/modelos.html', {'modelos': modelos })

def indices(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	indices_publicos = Raster.objects.filter(publica=True, isIndex=True, formula__isnull=False)
	meus_indices = Raster.objects.filter(publica=False, isIndex=True, responsavel=request.user)
	return render(request, 'preditor/indices.html', {'indices_publicos': indices_publicos,  'meus_indices':meus_indices})
def indice_new(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	erro = ""
	if request.method == "POST":
	    form = IndiceForm(request.user, request.POST)
	    if form.is_valid():
	        i = form.save(commit=False)
	        i.responsavel = request.user
	        i.isIndex = True
	        x = erroFormula(request.user, i.satelite, i.formula)
	        if x==False:
	        	if testeFormula(i.satelite, i.formula, i.tag):
	        		i.save()
	        		return redirect('indices')
	        	else:
	        		erro="A fórmula não executou"
	        else:
	        	erro = x
	else:
	    form = IndiceForm(request.user)
	rasters = Raster.objects.filter(isIndex=False, publica=True)
	rasters = list(rasters)
	r_resp = Raster.objects.filter(responsavel=request.user)
	for r in r_resp:
		rasters.append(r)
	list_sat = []
	list_rasters = []
	for rr in rasters:
		if list_sat.__contains__(rr.satelite):
			print("")
		else:
			list_r = []
			for rrr in rasters:
				if rrr.satelite == rr.satelite:
					list_r.append(rrr)
			list_sat.append(rr.satelite)
			list_rasters.append((rr.satelite, list_r))
	return render(request, 'preditor/indice_edit.html', {'form': form, 'rasters':rasters, 'list_rasters':list_rasters, 'erro':erro})

def indice_edit(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	i = Raster.objects.get(pk=pk)
	erro = ""
	if request.method == "POST":
	    form = IndiceForm(request.user, request.POST, instance=i)
	    if form.is_valid():
	        i = form.save(commit=False)
	        x = erroFormula(request.user, i.satelite, i.formula)
	        if x == False:
	        	if testeFormula(i.satelite, i.formula, i.tag):
	        		i.save()
	        		return redirect('indices')
	        	else:
	        		erro="A fórmula não executou"
	        else:
	        	erro = x
	else:
	    form = IndiceForm(request.user, instance=i)
	rasters = Raster.objects.filter(isIndex=False, publica=True)
	rasters = list(rasters)
	r_resp = Raster.objects.filter(responsavel=request.user, isIndex=False)
	for r in r_resp:
		rasters.append(r)
	list_sat = []
	list_rasters = []
	for rr in rasters:
		if list_sat.__contains__(rr.satelite):
			print("")
		else:
			list_r = []
			for rrr in rasters:
				if rrr.satelite == rr.satelite:
					list_r.append(rrr)
			list_sat.append(rr.satelite)
			list_rasters.append((rr.satelite, list_r))
	return render(request, 'preditor/indice_edit.html', {'form': form, 'rasters':rasters,'list_rasters':list_rasters, 'erro': erro})

def indice_testarFormula(request, pk=0):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	erro = ""
	sucesso = ""
	action = 'new'
	sensor = ""
	if pk!=0:
		i = Raster.objects.get(pk=pk)
		action = 'edit'
	if request.method == "POST":
		form = IndiceForm(request.user, request.POST)
		if pk != 0:
			form = IndiceForm(request.user, request.POST, instance=i)
		if form.is_valid():
			i = form.save(commit=False)
			sensor = i.satelite
			x = erroFormula(request.user, i.satelite, i.formula)
			if x == False:
				if testeFormula(i.satelite, i.formula, i.tag):
					sucesso = "Fómula validada!"
				else:
					erro = "A fórmula não executou"
			else:
				erro = x
	else:
		form = IndiceForm(request.user,instance=i)
	rasters = Raster.objects.filter(isIndex=False, publica=True)
	rasters = list(rasters)
	r_resp = Raster.objects.filter(responsavel=request.user)
	for r in r_resp:
		rasters.append(r)
	list_sat = []
	list_rasters = []
	for rr in rasters:
		if list_sat.__contains__(rr.satelite):
			print("")
		else:
			list_r = []
			for rrr in rasters:
				if rrr.satelite == rr.satelite:
					list_r.append(rrr)
			list_sat.append(rr.satelite)
			list_rasters.append((rr.satelite, list_r))
	return render(request, 'preditor/indice_edit.html', {'form': form, 'sensor':sensor, 'rasters':rasters, 'list_rasters':list_rasters, 'action': action, 'erro':erro, 'sucesso': sucesso})
def testeFormula(sat, formula, tag):
	path = os.getcwd() + '/arquivos/testes/'+sat.descricao
	src_ref = rasterio.open(path + '/cortes/'+sat.bandReferencia+'.tif')
	try:
		raster = calc.indice_calc_formula(src_ref, sat, formula, path)
	except:
		print("Erro na fórmula")
		return False
	calc.indice_write_tif(raster, src_ref, path +'/', tag)
	return True
def erroFormula(user, sat, formula):
	rasters = Raster.objects.filter(isIndex=False, publica=True, satelite=sat)
	rasters = list(rasters)
	r_resp = Raster.objects.filter(responsavel=user, satelite=sat)
	for r in r_resp:
		rasters.append(r)
	list_bands = []
	for lb in rasters:
		list_bands.append(lb.tagOnSat)
	list_formula = formula.split()
	list_r = []
	erro = False
	for char in list_formula:
		if len(char) > 1:
			if list_r.__contains__(char):
				continue
			else:
				if char in list_bands:
					print(char + " ok")
				else:
					print("Banda não reconhecida: "+char)
					erro = "Banda não reconhecida: "+char
				list_r.append(char)
		else:
			if char in ['(',')','+','-','*','/']:
				print(char + " ok")
			else:
				print("Erro no operador: " +char)
				erro = "Erro no operador: " +char
	return erro

def modelo_open(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = get_object_or_404(Modelo, pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	error = request.session.get('error')
	if error == None:
		error = ''
	else:
		del request.session['error']

	path = os.getcwd()+'/arquivos/modelos/'+modelo.pasta
	classes = ClasseModelo.objects.filter(modelo=modelo)
	sensor = Satelite.objects.get(pk=2)
	if modelo.sensor is not None:
		sensor = modelo.sensor
	else:
		modelo.sensor=sensor
		modelo.save()
	rasters = Raster.objects.filter(satelite=sensor)
	vars = []
	for r in rasters:
		rm = Raster_Modelo.objects.filter(modelo=modelo, raster=r)
		marked = False
		if len(rm)>0:
			marked = True
		v = Variavel(r.pk, r.tag, marked)
		vars.append(v)
	areas = []
	area_total = 0.0
	for classe in classes:
		areas2 = AreaModelo.objects.filter(classe=classe)
		if areas2:
			for area in areas2:
				areas.append(area)
				try:
					area_total = area_total+float(area.tamanho)
				except:
					print("area sem tamanho")

	#Listar Variávais
	listVars = []
	variaveis = VariavelModelo.objects.filter(modelo=modelo)
	for var in variaveis:
		listVars.append(var)

	#TODO listar repos só daquele sensor
	repos = utils.list_repositorios(modelo.stack)
	models = ArquivoModelo.objects.filter(modelo=modelo)
	tipo_models = TipoArquivoModelo.objects.all()
	repo_local=[]
	if modelo.sensor.pk>2:
		if os.path.isdir(path+'/repositorio/'):
			print("path Já Criado")
		else:
			os.mkdir(path+'/repositorio/')
		repo_local=utils.list_filesinfolder(path+'/repositorio/')

	target_ok = False
	y_ok = False
	status = "Dados não Preparados"
	for item in os.listdir(path):
		if item == "target_train.txt":
			target_ok = True
			print("achou target")
		if item == "target_train.txt":
			y_ok = True
			print("achou y")
	locale.setlocale(locale.LC_ALL, '')  # pega o local da máquina e seta o locale
	try:
		t = locale.format('%d', int(modelo.total_dados), 1)
	except:
		t = 0
	if (target_ok and y_ok):
		status = "Dados Preparados: "+str(t)+" de linhas. Treino ("+modelo.percent+"%)  e Teste ("+str(100-int(modelo.percent))+"%)"
	sensores = Satelite.objects.filter(publica=True)
	sensores = list(sensores)
	s_resp = Satelite.objects.filter(responsavel=request.user)
	for s in s_resp:
		sensores.append(s)
	limite_area = 1000000000 #m2
	return render(request, 'preditor/modelo_open.html', {'repo_local':repo_local, 'limite_area': limite_area,  'sensores':sensores, 'sensor':sensor, 'area_total':area_total,'status':status,'modelo':modelo, 'error':error, 'classes':classes, 'vars': vars, 'areas':areas, 'repos':repos, 'models':models, 'tipo_models':tipo_models, 'listVars':listVars})

def save_sensor(request, pk, pk_sensor):
	modelo = Modelo.objects.get(pk=pk)
	sensor = Satelite.objects.get(pk=pk_sensor)
	modelo.sensor=sensor
	modelo.save()
	return redirect('modelo_open', pk=pk)

def excluir_arquivo(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	arq = ArquivoModelo.objects.get(pk=pk)
	modelo = arq.modelo
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	filename = arq.tipo.filename + str(arq.id) + '.sav'
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/modelos/'
	os.remove(path_model + filename)
	arq.delete()
	return redirect('modelo_open', pk=modelo.pk)

def gerar_stacks_modelo (request, pk):
	#TODO: Verificar Tile do stack selecionado de acordo com a área geral
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	stack = ""
	vars = []
	rasters = []
	modelo = Modelo.objects.get(pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	rms = Raster_Modelo.objects.filter(modelo=modelo)
	for rm in rms:
		Raster_Modelo.delete(rm)
	for k, v in request.POST.lists():
		if k=='repo':
			print(v)
			stack = v[0]
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
	if stack=="":
		return redirect('modelo_open', pk)
	corte_ok, desc_erro = cortarModelo(pk, stack, rasters)
	if not corte_ok:
		request.session['error'] = desc_erro
	return redirect('modelo_open', pk=pk)

def prepararDataFrameModelo_Request(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = Modelo.objects.get(pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	percent = request.POST['percent']
	prepararDataFrameModelo(pk, percent)
	return redirect('modelo_open', pk=pk)
def prepararDataFrameModelo(pk, percent):
	modelo = Modelo.objects.get(pk=pk)
	s = "Sentinel" + modelo.stack[2:4]
	sat = modelo.sensor
	rms = Raster_Modelo.objects.filter(modelo=modelo)
	classes = ClasseModelo.objects.filter(modelo=modelo)
	areas = AreaModelo.objects.filter(classe__in=classes)

	target = pd.DataFrame()
	y = pd.Series()
	target_test = pd.DataFrame()
	y_test = pd.Series()
	total_dados = 0
	for area in areas:
		dfArea = pd.DataFrame()
		id = str(area.pk)
		print("Iniciando área" + id)
		for rm in rms:
			path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/' + id
			r = rm.raster
			nome = r.tag
			if r.isIndex:
				if r.formula is None:
					path = path + '/'
					nome = nome.lower()
				else:
					path = path + '/' + modelo.stack + '/indices/'
			else:
				path = path + '/' + modelo.stack + '/cortes/'
				nome = r.band
			raster = rasterio.open(path + nome + '.tif')
			array = raster.read(1)
			nn = np.array(array)
			val = nn.flatten()
			vv = pd.Series(val)
			dfArea[r.tag] = vv
		print(len(dfArea))
		dfArea = dfArea.dropna()
		if (len(dfArea)==0):
			erro = "Algum índice está retornando apenas valores nulos. - "+area.descricao
			print(erro)
			return
		area.classe.total_dados = int(area.classe.total_dados) + len(dfArea)
		area.classe.save()
		total_dados = total_dados + len(dfArea)
		train, test = train_test_split(dfArea, test_size=float(100-int(percent))/100)
		target = pd.concat([target, train])
		target_test = pd.concat([target_test, test])
		yArea_train = pd.Series([area.classe.classe] * len(train.index))
		yArea_test = pd.Series([area.classe.classe] * len(test.index))
		y = pd.concat([y, yArea_train])
		y_test = pd.concat([y_test, yArea_test])
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/'
	#target.reset_index(inplace=True)
	#Deletar variáveis antigas:
	mvs = VariavelModelo.objects.filter(modelo=modelo)
	for m in mvs:
		m.delete()
	print("Gerando arquivo target")
	delimiter =";"
	head = ''
	for item in target.columns:
		head = head + delimiter + item
		mv = VariavelModelo()
		mv.modelo=modelo
		mv.variavel=item
		mv.save()
	head = head[len(delimiter):]
	np.savetxt(r''+path_model+"target_train.txt", target.values, fmt='%4f', delimiter=delimiter, header=head)
	print("Gerando arquivo target test")
	np.savetxt(r'' + path_model + "target_test.txt", target_test.values, fmt='%4f', delimiter=delimiter, header=head)
	print("Gerando arquivo y")
	np.savetxt(r''+path_model+"y_train.txt", y.values, fmt='%s')
	print("Gerando arquivo y_test")
	np.savetxt(r'' + path_model + "y_test.txt", y_test.values, fmt='%s')
	modelo.percent = str(percent)
	modelo.total_dados = total_dados
	modelo.save()

def prepararDataFrameStack(modelo_treinado, area, stack):
	vrvs = VariavelModelo.objects.filter(modelo=modelo_treinado.modelo)
	#TODO: melhorar essa busca de satelite
	s = "Sentinel" + stack[2:4]
	sat = Satelite.objects.filter(descricao=s)[0]
	df = pd.DataFrame()
	for vr in vrvs:
		path = os.getcwd() + '/arquivos/projetos/' + area.projeto.pasta + '/' + area.pasta
		var = vr.variavel
		r = None
		rs = Raster.objects.filter(satelite=modelo_treinado.modelo.sensor, band=var)
		for r1 in rs:
			r = r1
		if len(rs)==0:
			rs = Raster.objects.filter(satelite=modelo_treinado.modelo.sensor, tag=var)
			for r1 in rs:
				r = r1
		nome = r.tag
		if r.isIndex:
			if r.formula is None:
				path = path + '/'
				nome = nome.lower()
			else:
				path = path + '/' + stack + '/indices/'
		else:
			path = path + '/' + stack + '/cortes/'
			nome = r.band
		raster = rasterio.open(path + nome + '.tif')
		array = raster.read(1)
		nn = np.array(array)
		val = nn.flatten()
		vv = pd.Series(val)
		df[r.tag] = vv
	df = df.dropna()
	return df, sat
def classificar(request, arq_pk, area_pk, stack):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	area = Area.objects.get(pk=area_pk)
	modelo_treinado = ArquivoModelo.objects.get(pk=arq_pk)
	if modelo_treinado.modelo.responsavel != request.user:
		return redirect('modelos')
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	modelo = ia.ler_modelo_arquivo(modelo_treinado)
	df, sat = prepararDataFrameStack(modelo_treinado, area, stack)
	print(df.shape)
	result = ia.classificar(modelo, df)
	path_corte = os.getcwd() + '/arquivos/projetos/' + area.projeto.pasta + '/' + area.pasta + '/' + stack + '/cortes/'
	bandReferencia = rasterio.open(path_corte+sat.bandReferencia+'.tif')
	path = os.getcwd() + '/arquivos/projetos/' + area.projeto.pasta + '/' + area.pasta + '/' + stack + '/classificacao'
	if os.path.isdir(path):
		print("path Já Criado")
	else:
		os.mkdir(path)
	path = os.getcwd() + '/arquivos/projetos/' + area.projeto.pasta + '/' + area.pasta + '/' + stack + '/classificacao/' + str(
		modelo_treinado.pk) + '/'
	if os.path.isdir(path):
		print("path Já Criado")
	else:
		os.mkdir(path)
	m = modelo_treinado.modelo
	classes = ClasseModelo.objects.filter(modelo=m)
	classes2 = []
	numeros = []
	i = 1
	for classe in classes:
		classes2.append(classe.classe)
		numeros.append(i)
		i = i + 1
	classes_num = pd.DataFrame()
	classes_num['num'] = numeros
	classes_num['classe'] = classes2
	classes_num = classes_num.set_index('classe')
	result_num = []
	for r in result:
		result_num.append(classes_num.loc[r,'num'])
	filename= "Classificador"
	try:
		filename = modelo_treinado.tipo.filename
	except:
		print("não há tipo arquivo")
	y = pd.Series(result)
	print(y.head())
	print(len(y))
	tabela = y.value_counts()
	ind = tabela.index
	print(len(tabela))
	i = 0
	dcs = DadosClassificacao.objects.filter(area = area, arquivoModelo = modelo_treinado, stack = stack)
	for d in dcs:
		d.delete()
	while i < len(tabela):
		dc = DadosClassificacao()
		dc.area = area
		dc.arquivoModelo = modelo_treinado
		dc.stack = stack
		dc.classe = ind[i]
		dc.quantidade = tabela[i]
		dc.save()
		i = i + 1
	print(result_num.__len__())
	gerarTiffPorDataFrame(result_num, path, bandReferencia, filename)
	return redirect('classificar_page', arq_pk, area_pk, stack)

def gerarTiffPorDataFrame(pd, path, rasterReferencia, name="Classificador"):
	band_geo = rasterReferencia.profile
	array = rasterReferencia.read()
	array_classe = []
	l = 0
	for i in array:
		ii = []
		for j in i:
			jj = []
			for k in j:
				if k!=0:
					try:
						k=pd[l]
					except:
						print(l)
					l=l+1

				jj.append(k)
			ii.append(jj)
		array_classe.append(ii)
	array_classe = np.array(array_classe)
	print("criando rgb.tiff...")
	with rasterio.open(path + name+'.tif', 'w', **band_geo) as dest:
		dest.write(array_classe)
def treinar_Request(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = Modelo.objects.get(pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	percent = request.POST['percent']
	max_depth = int(request.POST['max_depth'])
	loop_cross = int(request.POST['loop_cross'])
	for k, v in request.POST.lists():
		if k.startswith('model_'):
			id = k[6:]
			treinar(percent,pk, int(id), max_depth, loop_cross)
	return redirect('modelo_open', pk=pk)
def treinar(percent, pk, pk_me, max_depth, loop_cross):
	modelo = Modelo.objects.get(pk=pk)
	path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta
	target_ok = False
	y_ok = False
	for item in os.listdir(path):
		if item == "target_train.txt":
			target_ok = True
			print("achou target")
		if item == "target_train.txt":
			y_ok = True
			print("achou y")
	if(target_ok and y_ok):
		print("Arquivos já gerados")
	else:
		prepararDataFrameModelo(pk,percent)
	#ler arquivos
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/'
	print("Lendo target")
	target = np.loadtxt(r''+path_model+"target_train.txt", delimiter=";")
	print("Lendo y")
	y = np.loadtxt(r''+path_model+"y_train.txt", dtype='str', delimiter=";")
	#Treinar Modelo
	print("Treinando modelo" + str(pk_me))
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/modelos/'
	if os.path.isdir(path_model):
		print("path Já Criado")
	else:
		os.mkdir(path_model)
	tipo = TipoArquivoModelo.objects.get(pk=pk_me)
	list_cols = []
	vms = VariavelModelo.objects.filter(modelo=modelo)
	for vm in vms:
		list_cols.append(vm.variavel)
	model, importance = ia.treinar_modelo(target, y, tipo, max_depth, list_cols)
	rms = Raster_Modelo.objects.filter(modelo=modelo)
	print("Salvando arquivo")
	#salvar treinamento
	arq_modelo = ArquivoModelo()
	arq_modelo.tipo = tipo
	arq_modelo.modelo = modelo
	arq_modelo.data_treinamento = timezone.now()
	if tipo.tag == "rf":
		arq_modelo.max_depth = max_depth
	arq_modelo.save()
	print("Salvando Importancias")
	list = []
	variaveis = VariavelModelo.objects.filter(modelo=modelo)
	for vv in variaveis:
		list.append(vv)
	for i, v in enumerate(importance):
		imp = ImportanciaVariavel()
		imp.arquivoModelo = arq_modelo
		imp.variavel = list[i]
		imp.importancia = v
		imp.save()
	filename = tipo.filename + str(arq_modelo.id) + '.sav'
	joblib.dump(model, path_model + filename)
	validar(loop_cross, arq_modelo)
def validar(loop_cross, arq_modelo):
	modelo = arq_modelo.modelo
	path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta
	tipo = arq_modelo.tipo
	model = ia.ler_modelo_arquivo(arq_modelo)
	# ler arquivos
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/'
	print("Lendo target")
	target = np.loadtxt(r'' + path_model + "target_train.txt", delimiter=";")
	print("Lendo y")
	y = np.loadtxt(r'' + path_model + "y_train.txt", dtype='str', delimiter=";")
	mean, menor, maior = ia.validar_modelo(model, target, y, loop_cross)
	#salvar teste
	arq_modelo.loop_cross = loop_cross
	arq_modelo.acuraciaTreinoMedia = mean
	arq_modelo.acuraciaTreinoMenor = menor
	arq_modelo.acuraciaTreinoMaior = maior
	arq_modelo.save()

def testar(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	arq_modelo = ArquivoModelo.objects.get(pk=pk)
	modelo = arq_modelo.modelo
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta
	tipo = arq_modelo.tipo
	model = ia.ler_modelo_arquivo(arq_modelo)
	# ler arquivos
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/'
	print("Lendo target")
	target_test = np.loadtxt(r'' + path_model + "target_test.txt", delimiter=";")
	print("Lendo y")
	y_test = np.loadtxt(r'' + path_model + "y_test.txt", dtype='str', delimiter=";")
	result = ia.testar_modelo(model, target_test, y_test)
	#salvar teste
	arq_modelo.data_teste = timezone.now()
	arq_modelo.acuraciaTeste = "%.5f" % (result * 100)
	arq_modelo.save()
	return redirect('modelo_open', pk=modelo.pk)

def ver_stacks_modelo (request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = Modelo.objects.get(pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
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
		for dirpath, dirnames, filenames in os.walk(os.getcwd() + '/arquivos/modelos/'+modelo.pasta+'/'+str(area.pk)+'/'+stack+'/'):
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
		for dirpath, dirnames, filenames in os.walk(os.getcwd() + '/arquivos/modelos/'+modelo.pasta+'/'+str(area.pk)+'/'):
			for file in filenames:
				tipo = "Indice"
				if file[-4:] == '.png':
					continue
				else:
					if file=="declividade.tif":
						tipo="Declividade"
						arqs.append(Arquivo(file, tipo))
					if file=="altitude.tif":
						tipo="Altitude"
						arqs.append(Arquivo(file, tipo))

		areaList = AreaList(area.pk, area.descricao, arqs)
		list.append(areaList)
	return render(request, 'preditor/modelo_stacks.html', {'modelo':modelo, 'list':list})

def modelo_new(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	if request.method == "POST":
		form = ModeloForm(request.POST)
		if form.is_valid():
			modelo = form.save(commit=False)
			modelo.responsavel = request.user
			modelo.data_criacao = timezone.now()
			pasta=secrets.token_hex(nbytes=6)
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
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = Modelo.objects.get(pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
	pasta_old = modelo.pasta
	if request.method == "POST":
		form = ModeloForm(request.POST, instance=modelo)
		if form.is_valid():
			modelo = form.save(commit=False)
			modelo.save()
			return redirect('modelo_open', pk=modelo.pk)
	else:
		form = ModeloForm(instance=modelo)
	return render(request, 'preditor/modelo_edit.html', {'form': form})

def var_modelo_edit(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	var_modelo = VariavelModelo.objects.get(pk=pk)
	if var_modelo.modelo.responsavel!=request.user:
		return redirect('modelos')
	if request.method == "POST":
		form = VariavelModeloForm(request.POST, instance=var_modelo)
		if form.is_valid():
			var_modelo = form.save(commit=False)
			var_modelo.save()
			return redirect('modelo_open', pk=var_modelo.modelo.pk)
	else:
		form = VariavelModeloForm(instance=var_modelo)
	return render(request, 'preditor/modelo_edit.html', {'form': form})

def classe_modelo_new(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = get_object_or_404(Modelo, pk=pk)
	if modelo.responsavel!=request.user:
		return redirect('modelos')
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
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	classe = get_object_or_404(ClasseModelo, pk=pk)
	modelo = classe.modelo
	if modelo.responsavel != request.user:
		return redirect('modelos')
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
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	modelo = get_object_or_404(Modelo, pk=pk)
	if modelo.responsavel != request.user:
		return redirect('modelos')
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
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	area = get_object_or_404(AreaModelo, pk=pk)
	if area.classe.modelo.responsavel != request.user:
		return redirect('modelos')
	classe = area.classe
	error = request.session.get('error')
	if error == None:
		error = ''
	else:
		del request.session['error']
	path = os.getcwd()+'/arquivos/modelos/'+area.classe.modelo.pasta+'/masks/'
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
			location = obj['coordinates'][0][0]
			area_m = c_area(obj)
			m = folium.Map(
        		location=[location[1], location[0]],
        		tiles="cartodbpositron",
        		zoom_start=10,
        		)
			folium.GeoJson(mask, name=area.descricao).add_to(m)
			folium.LayerControl().add_to(m)
			m=m._repr_html_()
	return render(request, 'preditor/area_modelo_edit.html', {'form': form, 'modelo':area.classe.modelo, 'area':area, 'my_map': m, 'error':error})

def projetos(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	projetos = Projeto.objects.filter(responsavel=request.user)
	return render(request, 'preditor/projetos.html', {'projetos': projetos})

def projeto_open(request, pk, ancora="p4"):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	projeto = get_object_or_404(Projeto, pk=pk)
	if projeto.responsavel != request.user:
		return redirect('projetos')
	error = request.session.get('error')
	if error == None:
		error = ''
	else:
		del request.session['error']
	areas = Area.objects.filter(projeto=projeto)
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta
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
	return render(request, 'preditor/projeto_open.html', {'projeto':projeto, 'areas':areas, 'shapes':shapes, 'error':error})

def area_open(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	area = Area.objects.get(pk=pk)
	projeto = area.projeto
	if projeto.responsavel != request.user:
		return redirect('projetos')
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	mask = path+"/mask/"+str(area.pk)+".geojson"
	#calculando área m2
	if os.path.isfile(mask):
		print("mask ok")
	else:
		return redirect('projeto_open', pk=projeto.pk)
	with open(mask) as data_file:
		geoms= json.loads(data_file.read())
	obj = geoms['features'][0]['geometry']
	location = obj['coordinates'][0][0]
	area_m = c_area(obj)
	m = folium.Map(
		location=[location[1], location[0]],
		tiles="cartodbpositron",
		zoom_start=10,
	)
	folium.GeoJson(mask, name=area.descricao).add_to(m)
	folium.LayerControl().add_to(m)
	m=m._repr_html_()
	dec = glob.glob(path+'/declividade.tif')
	alt = glob.glob(path+'/altitude.tif')
	try:
		tiles = utils.verificar_tile_mask(mask)
	except:
		print("Erro na leitura dos Tiles!!!")
		tiles = []
	if len(tiles) == 1:
		repos = utils.list_repositorios(tile = tiles[0])
	else:
		repos = utils.list_repositorios()
	limite_area = 1000000000  # m2
	return render(request, 'preditor/area_open.html', {'tiles':tiles, 'mask':mask, 'limite_area':limite_area, 'projeto':projeto, 'area':area, 'my_map': m, 'dec':dec, 'alt':alt, 'repos':repos, 'area_m':area_m})

def stack(request, pk, stack):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	area = Area.objects.get(pk=pk)
	projeto = area.projeto
	if projeto.responsavel != request.user:
		return redirect('projetos')
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	sensor = Satelite.objects.get(descricao="Sentinel"+repo.level)
	r_indices = Raster.objects.filter(isIndex=True, publica=True, formula__isnull=False, satelite=sensor)
	meus_indices = Raster.objects.filter(isIndex=True, publica=False, formula__isnull=False, responsavel=request.user, satelite=sensor)
	r_indices = list(r_indices)
	for m in meus_indices:
		r_indices.append(m)

	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'+stack
	l = len(path+'/cortes')
	cortes = []
	for dirpath, dirnames, filenames in os.walk(path+'/cortes'):
		for file in filenames:
			arquivo = Arquivo("","")
			arquivo.tipo = file[-3:]
			if (arquivo.tipo == "tif"):
				arquivo.desc = file[:-4]
				cortes.append(arquivo)
	indices = []
	if len(cortes) > 0:
		l = len(path+'/indices')
		for dirpath, dirnames, filenames in os.walk(path+'/indices'):
			for file in filenames:
				arquivo = Arquivo("","")
				arquivo.tipo = file[-3:]
				if (arquivo.tipo == "tif"):
					arquivo.desc = file
					indices.append(arquivo)
	modelos = Modelo.objects.filter(responsavel=request.user)
	modelos_treinados = ArquivoModelo.objects.filter(modelo__in=modelos)
	return render(request, 'preditor/stack.html', {'projeto':projeto, 'area':area, 'indices':indices, 'r_indices':r_indices, 'cortes': cortes, 'repo':repo, 'modelos_treinados':modelos_treinados })

def classificar_page(request, arq_pk, area_pk, stack):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	area = Area.objects.get(pk=area_pk)
	projeto = area.projeto
	if projeto.responsavel != request.user:
		return redirect('projetos')
	modelo_treinado = ArquivoModelo.objects.get(pk=arq_pk)
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	classificacoes = []
	for dirpath, dirnames, filenames in os.walk(path+'/'+stack+'/classificacao/'+str(arq_pk)):
		for file in filenames:
			arquivo = Arquivo("","")
			arquivo.tipo = file[-3:]
			if (arquivo.tipo == "tif"):
				arquivo.desc = file
				classificacoes.append(arquivo)
	vars_stack = []
	for dirpath, dirnames, filenames in os.walk(path+'/'+stack):
		for file in filenames:
			if (file[-3:] == "tif"):
				var = file[:-4]
				rs = Raster.objects.filter(satelite=modelo_treinado.modelo.sensor, band=var)
				for r in rs:
					var = r.tag
				vars_stack.append(var)
	for item in os.listdir(path):
		if (item[-3:] == "tif"):
			vars_stack.append(item[:-4].capitalize())
	variaveis_modelo = VariavelModelo.objects.filter(modelo=modelo_treinado.modelo)
	vars_modelo = []
	valido = True
	for r in variaveis_modelo:
		ok = vars_stack.__contains__(r.variavel)
		if ok == False:
			valido = False
		var = Arquivo(r.variavel, ok)
		vars_modelo.append(var)
	dcs = DadosClassificacao.objects.filter(area=area, arquivoModelo=modelo_treinado, stack=stack)
	pxtotal = 0
	for dc in dcs:
		pxtotal = pxtotal + int(dc.quantidade)
		arq = dc.arquivoModelo
	classes = ClasseModelo.objects.filter(modelo=arq.modelo)
	cores=[]
	for c in classes:
		cores.append(c.cor + c.classe)
	return render(request, 'preditor/classificar.html', {'projeto':projeto, 'cores':cores, 'pxtotal':pxtotal, 'dcs':dcs, 'area':area, 'valido':valido, 'classificacoes':classificacoes, 'repo':repo, 'modelo_treinado':modelo_treinado, 'vars_modelo':vars_modelo })

def projeto_new(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	if request.method == "POST":
		form = ProjetoForm(request.POST)
		if form.is_valid():
			projeto = form.save(commit=False)
			projeto.responsavel = request.user
			projeto.data_criacao = timezone.now()
			pasta=secrets.token_hex(nbytes=6)
			projeto.pasta = pasta
			os.mkdir('arquivos/projetos/'+pasta)
			os.mkdir('arquivos/projetos/'+pasta+'/temp')
			projeto.save()
			return redirect('projeto_open', pk=projeto.pk)
	else:
		form = ProjetoForm()
	return render(request, 'preditor/projeto_edit.html', {'form': form})

def area_new(request, pk):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	projeto = get_object_or_404(Projeto, pk=pk)
	if projeto.responsavel != request.user:
		return redirect('projetos')
	if request.method == "POST":
		form = AreaForm(request.POST)
		if form.is_valid():
			area = form.save(commit=False)
			area.responsavel = request.user
			area.data_criacao = timezone.now()
			area.projeto = projeto
			pasta=secrets.token_hex(nbytes=6)
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
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	m = folium.Map(
		location=[-14.7494, -48.6202],
		tiles="cartodbpositron",
		zoom_start=6,
	)
	draw = Draw(
		export=True,
		draw_options={'polygon':{'showArea':True}}, 
		edit_options= {
			'selectedPathOptions':{
				'maintainColor': True,
				'opacity': 0.3}
				},
		filename='desenho.geojson')
	draw.add_to(m)
	m=m._repr_html_()

	return render(request, 'preditor/draw.html', {'my_map': m})

def download_page(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	repos = utils.list_repositorios()
	mask = None
	area_m = None
	m = None
	data_ini = (datetime.today().date()-timedelta(days=3)).isoformat()
	data_fim = datetime.today().date().isoformat()
	if request.method == "POST":
		mask_hidden = request.POST['mask_hidden']
		if mask_hidden:
			mask = mask_hidden
			# calculando área m2
			if os.path.isfile(mask):
				print("mask ok")
			else:
				return redirect('download_page')
			with open(mask) as data_file:
				geoms = json.loads(data_file.read())
			obj = geoms['features'][0]['geometry']
			location = obj['coordinates'][0][0]
			area_m = c_area(obj)
			m = folium.Map(
				location=[location[1], location[0]],
				tiles="cartodbpositron",
				zoom_start=10,
			)
			folium.GeoJson(mask, name="area corte").add_to(m)
			folium.LayerControl().add_to(m)
			m = m._repr_html_()
	return render(request, 'preditor/download_page.html', {'mask': mask, 'data_ini':data_ini, 'data_fim':data_fim, 'area_m': area_m, 'my_map': m, 'repos':repos})

def trescores_page(request):
	return render(request, 'preditor/trescores_page.html', {})

def progressos(request):
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	progressos = BarraProgresso.objects.filter(usuario=request.user, data_finalizacao__isnull=True).order_by('-data_criacao')
	return render(request, 'preditor/progressos.html', {'progressos' : progressos})

def ndvi_page(request):
	request.session['hash_progress'] = hash("ndvi"+str(timezone.now()))
	return render(request, 'preditor/ndvi_page.html', {})

def user(request):
    return render(request, 'preditor/user.html', {})






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
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/mask/'
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
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/mask/'
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

def uploadImageRepositorio(request, pk):
	modelo = Modelo.objects.get(pk=pk)
	if (request.FILES.get('imagem', False)==False):
		request.session['error']='Adicione um arquivo de Imagem!'
		return redirect('/modelo/'+str(pk)+'/')
	imagem = request.FILES['imagem']
	tipo = request.POST['tipoImagem']
	path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/repositorio/'
	if os.path.isdir(path):
		print("path Já Criado")
	else:
		os.mkdir(path)
	im = Image.open(imagem)
	if im.getexif():
		print(im.getexif())
	else:
		request.session['error'] = 'Adicione uma Iamegm Georeferenciada!'
		return redirect('/modelo/' + str(pk) + '/')
	if im.getbands() == ('R', 'G', 'B'):
		im1 = Image.Image.split(im)
		im1[0].save(path + "RED" + str(imagem)[-4:])
		im1[1].save(path + "GREEN" + str(imagem)[-4:])
		im1[2].save(path + "BLUE" + str(imagem)[-4:])
	else:
		if tipo == "RGB":
			request.session['error'] = 'Selecione uma banda para a imagem!'
			return redirect('/modelo/' + str(pk) + '/')
		else:
			im.save(path+ tipo+str(imagem)[-4:])
	return redirect('/modelo/' + str(pk) + '/')
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
	path = os.getcwd()+'/arquivos/modelos/'+modelo.pasta+'/masks/'
	with default_storage.open(path+str(pk)+'.geojson', 'wb+') as destination:
		for chunk in mask.chunks():
			destination.write(chunk)
	with open(path+str(pk)+'.geojson') as data_file:
		geoms = json.loads(data_file.read())
	obj = geoms['features'][0]['geometry']
	area_m = c_area(obj)
	area.tamanho = str(area_m)
	area.save()
	return redirect('/area_modelo/'+str(area.pk))

def upload_modelo(request):
	return render(request, 'preditor/upload_modelo.html', {})
def upload_modelo_save(request):
	#TODO:Validar!!! Campos obrigatórios e cores diferentes
	if not request.user.is_authenticated:
		return redirect('accounts/login')
	if request.POST['nome_modelo'] == "":
		return render(request, 'preditor/upload_modelo.html', {})
	modelo = Modelo()
	modelo.descricao = request.POST['nome_modelo']
	modelo.responsavel = request.user
	modelo.data_criacao = timezone.now()
	pasta = secrets.token_hex(nbytes=6)
	os.mkdir('arquivos/modelos/' + pasta)
	modelo.pasta=pasta
	modelo.upload = True
	modelo.save()
	# salvar treinamento
	arq_modelo = ArquivoModelo()
	arq_modelo.modelo = modelo
	arq_modelo.save()
	for k, v in request.POST.lists():
		if k[:4] == 'cor_':
			classe = ClasseModelo()
			classe.modelo = modelo
			classe.cor = v[0]
			classe.classe = k[4:]
			classe.save()
		if k[:4] == 'var_':
			vari = VariavelModelo()
			vari.modelo = modelo
			vari.variavel = v[0]
			vari.save()
	path_model = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/modelos/'
	if os.path.isdir(path_model):
		print("path Já Criado")
	else:
		os.mkdir(path_model)
	print("Salvando arquivo")
	#tipo = request.POST['tipo']
	filename = str(arq_modelo.id) + '.sav'
	filename_temp = request.POST['arquivo']
	path_temp = os.getcwd() + '/arquivos/temp/'
	arquivo = open(path_temp + filename_temp)
	model = ia.ler_modelo_up(path_temp + filename_temp)
	joblib.dump(model, path_model + filename)
	return redirect('modelos')
def uploadArquivoModelo(request):
	if (request.FILES.get('modelo', False)==False):
		request.session['error']='Adicione um arquivo .sav!'
		return redirect('/upload_modelo')
	arquivo = request.FILES['modelo']
	modelo = ia.ler_modelo_up(arquivo)
	listVars=[]
	try:
		listVars = modelo.feature_names_in_
	except:
		rangeV = range(1, modelo.n_features_in_+1)
		for r in rangeV:
			listVars.append("var_"+str(r))
	path_temp = os.getcwd() + '/arquivos/temp/'
	filename_temp = secrets.token_hex(nbytes=6)
	filename_temp = filename_temp + ".sav"
	with open(path_temp+filename_temp, 'wb+') as destination:
		for chunk in arquivo.chunks():
			destination.write(chunk)
	return render(request, 'preditor/upload_modelo.html', {'modelo':modelo, 'arquivo':filename_temp, 'listVars': listVars})
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
	path = os.getcwd()+'/arquivos/modelos/'+modelo.pasta+'/masks/'
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
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'+stack
	path_mask = os.getcwd() + '/arquivos/projetos/' + projeto.pasta + '/' + area.pasta + '/mask/'
	corte_ok = corte(id, repo, path, path_mask)
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
		path_area = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/' + id
		path_modelo = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/'
		if os.path.isdir(path_area):
			print("path Já Criado")
		else:
			os.mkdir(path_area)
		path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/' + id + '/' + stack
		corte_ok = corte(id, repo, path, path_modelo+'masks/')
		if corte_ok:
			for r in rasters:
				if r.isIndex:
					if r.tag == 'Declividade':
						print("Cortando Declividade")
						utils.cortar_tif(path_modelo + 'masks/', id,
										 'repositorio/topodata/declividade_caldas.tif',
										 path_area+'/declividade.tif')
					if r.tag == 'Altitude':
						print("Cortando Altitude")
						utils.cortar_tif(path_modelo + 'masks/', id,
										 'repositorio/topodata/altitude_caldas.tif',
										 path_area+'/altitude.tif')
					if (r.tag != 'Declividade' and r.tag != 'Altitude'):
						print("Gerando Índice" + r.tag)
						s = "Sentinel"+repo.level
						sats = Satelite.objects.filter(descricao=s)
						sat = None
						for s in sats:
							sat = s
						src_ref = rasterio.open(path+'/cortes/'+modelo.sensor.bandReferencia+'.tif')
						raster = calc.indice_calc_formula(src_ref, sat, r.formula, path)
						calc.indice_write_tif(raster, src_ref, path +'/indices/', r.tag)
			print("Finalizado ")
		else:
			print("Erro ao cortar! Imagens fora da área de corte!")
			return False, "Erro ao cortar! Imagens fora da área de corte! Área: "+area.descricao
	return True, ""
def corte(id, repo, path, path_mask):
	print(path_mask)
	t_file_name = -11
	if (repo.level == '1C'):
		t_file_name = -7
	#### criar pastas
	if os.path.isdir(path):
		print("path Já Criado")
	else:
		os.mkdir(path)
		os.mkdir(path + '/cortes')
		os.mkdir(path + '/indices')
	#### Cortar com gdal
	# es_obj = {'a':...,'b':..., 'c':...}
	kwargs = utils.montar_kwargs_gdal(path_mask, id)
	rasters = []
	# gdal.SetConfigOption('GDAL_HTTP_UNSAFESSL', 'YES')
	listRastes = []
	if repo.level == 'RG':
		sat = Satelite.objects.get(descricao="Visível RGB")
		lista = Raster.objects.filter(isIndex=False, publica=True, satelite=sat)
		for r in lista:
			listRastes.append(r.band)
		for dirpath, dirnames, filenames in os.walk(path+'/../../repositorio'):
			for file in filenames:
				if listRastes.__contains__(file[t_file_name:-4]):
					input = dirpath + '/' + file
					out = path + '/cortes/' + file[t_file_name:-4] + '.tif'
					processo = gdal.Warp(srcDSOrSrcDSTab=input, destNameOrDestDS=out, **kwargs)
					print(os.path.getsize(out))
					if os.path.getsize(out) < 500:
						return False
	else:
		path_input = ''
		path_input = utils.path_repositorio(repo.level, repo.data)
		l = len(path)
		desc_sat = "Sentinel"+repo.level
		sat = Satelite.objects.get(descricao=desc_sat)
		lista = Raster.objects.filter(isIndex=False, publica=True, satelite=sat)
		for r in lista:
			listRastes.append(r.band)
		#if repo.level == "1C":
		#	ListRastes = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12']
		#if repo.level == "2A":
		#	ListRastes = ['B01_20m','B02_10m','B03_10m','B04_10m','B05_20m','B06_20m','B07_20m','B08_10m','B8A_20m','B09_60m','B11_20m','B12_20m','AOT_10m','SCL_20m','TCI_10m','WVP_10m',]
		for dirpath, dirnames, filenames in os.walk(path_input):
			for file in filenames:
				if (len(file) > 8):
					if (file[-4:] == '.jp2'):
						if listRastes.__contains__(file[t_file_name:-4]):
							if dirpath[-7:] != "QI_DATA":
								input = dirpath + '/' + file
								out = path + '/cortes/' + file[t_file_name:-4] + '.tif'
								processo = gdal.Warp(srcDSOrSrcDSTab=input,
									  destNameOrDestDS=out, **kwargs, xRes=10, yRes=10)
								print(os.path.getsize(out))
								if os.path.getsize(out) < 500:
									return False
	return True
def progress_callback(complete, message, self):
	percent = math.floor(complete * 100)



def declividade_gerar(request, pk):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	path = 'arquivos/projetos/'+projeto.pasta+'/'+area.pasta
	kwargs = utils.montar_kwargs_gdal(path+'/mask/', str(area.pk))


	"""
	### buscar extremidades máscara
	path_mask = path+'/mask/'+str(area.pk)+'.geojson'
	max_lat, min_lat, max_long, min_long = utils.extremidades_mascara(path_mask)
	### percirrer rasters topodata
	path_topo = 'repositorio/topodata/'
	r_input = 'C_17S495SN.tif'
	for dirpath, dirnames, filenames in os.walk(path_topo):
		for file in filenames:
			if (file[-6:] == 'SN.tif'):
				with rasterio.open(path_topo+file) as src:
					band1 = src.read(1)
					height = band1.shape[0]
					width = band1.shape[1]
					cols, rows = np.meshgrid(np.arange(width), np.arange(height))
					xs, ys = rasterio.transform.xy(src.transform, rows, cols)
					lons = np.array(xs)
					lats = np.array(ys)
					r_max_long = lons.max()
					r_min_long = lons.min()
					r_max_lat = lats.max()
					r_min_lat = lats.min()
					if (max_lat<r_max_lat):
						if (min_lat>r_min_lat):
							if (max_long<r_max_long):
								if (min_long>r_min_long):
									print("achei")
									r_input = file
									break
	input = path_topo+r_input
	gdal.SetConfigOption('CHECK_DISK_FREE_SPACE', 'FALSE')
	"""
	#versão valida
	input = 'repositorio/topodata/declividade_caldas.tif'

	out =  path+'/declividade.tif'
	ds = gdal.Warp(srcDSOrSrcDSTab = input,
         destNameOrDestDS=out,
		 **kwargs)
	print("cortado")
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

def preparar_download_sentinel(request):
	data_ini = request.POST['data_ini']
	data_fim = request.POST['data_fim']
	sat = request.POST['satelite']
	d_ini = ''.join(filter(lambda i: i not in "-", data_ini))
	d_fim = ''.join(filter(lambda i: i not in "-", data_fim))
	mask_hidden = request.POST['mask_hidden']
	path_mask = mask_hidden
	if path_mask == 'None':
		mask = request.FILES['mask']
		name = secrets.token_hex(nbytes=4)
		with default_storage.open(name + '.geojson', 'wb+') as destination:
			for chunk in mask.chunks():
				destination.write(chunk)
		path_mask = 'arquivos/' + name + '.geojson'
	api = SentinelAPI('juanmorysson', 'Blow642Sock095#', 'https://scihub.copernicus.eu/dhus')
	footprint = geojson_to_wkt(read_geojson(path_mask))
	products = api.query(footprint,
						 platformname='Sentinel-2',
						 producttype=sat,
						 #cloudcoverpercentage=(0, 30),
						 date=(d_ini, d_fim))
	products_df = api.to_dataframe(products)
	prds = []
	if len(products_df)>0:
		prds = products_df.loc[:,"title"]

	mask = path_mask
	# calculando área m2
	if os.path.isfile(mask):
		print("mask ok")
	else:
		return redirect('download_page')
	with open(mask) as data_file:
		geoms = json.loads(data_file.read())
	obj = geoms['features'][0]['geometry']
	location = obj['coordinates'][0][0]
	area_m = c_area(obj)
	m = folium.Map(
		location=[location[1], location[0]],
		tiles="cartodbpositron",
		zoom_start=10,
	)
	folium.GeoJson(mask, name="area corte").add_to(m)
	folium.LayerControl().add_to(m)
	m = m._repr_html_()
	return render(request, 'preditor/download_page.html', {'mask':mask,'area_m':area_m, 'my_map': m,'data_ini': data_ini, 'data_fim': data_fim,'satelite':sat, 'prds':prds})

def download_sentinel(request):
	data_ini = request.POST['data_ini']
	data_fim = request.POST['data_fim']
	sat = request.POST['satelite']
	data_ini = ''.join(filter(lambda i: i not in "-", data_ini))
	data_fim = ''.join(filter(lambda i: i not in "-", data_fim))
	mask_hidden = request.POST['mask_hidden']
	if mask_hidden:
		path_mask = mask_hidden
	else:
		mask = request.FILES['mask']
		name = secrets.token_hex(nbytes=4)
		with default_storage.open(name+'.geojson', 'wb+') as destination:
			for chunk in mask.chunks():
				destination.write(chunk)
		path_mask = 'arquivos/'+name+'.geojson'
	api = SentinelAPI('juanmorysson', 'Blow642Sock095#', 'https://scihub.copernicus.eu/dhus')
	footprint = geojson_to_wkt(read_geojson(path_mask))
	products = api.query(footprint,
						 platformname='Sentinel-2',
						 producttype=sat,
						 #cloudcoverpercentage=(0, 30),
						 date=(data_ini, data_fim))
	'''
	tiles = ['22KGF',]
	query_kwargs = {
        'platformname': 'Sentinel-2',
        'producttype': 'S2MSI1C',
        'date': (data_ini, data_fim)}
	#'date': ('NOW-14DAYS', 'NOW')}
	products = OrderedDict()
	for tile in tiles:
	    kw = query_kwargs.copy()
	    kw['tileid'] = tile
	    pp = api.query(**kw)
	    products.update(pp)
	'''
	api.download_all(products, directory_path='repositorio/sentinel/')
	print("XXXXXXXXXXX Inciando unzip")
	#unzip downloads
	path = os.getcwd()+'/repositorio/sentinel/'
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
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'+stack
	progresso = progress.progress_create(projeto, "ndvi", request)
	if progresso:
		print(progresso.hash)
	progress.progress_save(5, "lendo arquivos...", progresso)
	nome = 'ndvi'
	print(timezone.now())
	print("lendo arquivos...")

	src_red = rasterio.open(path+'/cortes/B04.tif')
	src_nir = rasterio.open(path+'/cortes/B08.tif')
	####NDVI
	progress.progress_save(15, "Calculando NDVI - isso pode demorar...", progresso)
	ndvi = calc.ndvi(src_red, src_nir)

	progress.progress_save(60, "Escrevendo Imagem", progresso)
	calc.ndvi_write(ndvi, src_red, path+'/indices/', nome)

	progress.progress_save(100, "Concluído", progresso)

	return redirect('stack', pk, stack) 

def gerar_indices_area(request, pk, stack):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'+stack
	s = "Sentinel" + repo.level
	sats = Satelite.objects.filter(descricao=s)
	sat = None
	for s in sats:
		sat = s
	for k, v in request.POST.lists():
		if k.startswith('ind_'):
			ipk = k[4:len(k)]
			r = Raster.objects.get(pk=int(ipk))
			try:
				src_ref = rasterio.open(path + '/cortes/' + sat.bandReferencia + '.tif')
			except:
				return redirect('stack', pk, stack)
			raster = calc.indice_calc_formula(src_ref, sat, r.formula, path)
			calc.indice_write_tif(raster, src_ref, path + '/indices/', r.tag)

	return redirect('stack', pk, stack)
def gerar_indice_area(request, pk, stack, pk_indice):
	area = Area.objects.get(pk=pk)
	projeto = Projeto.objects.get(pk=area.projeto.pk)
	repo = RepoSentinel()
	repo.level = stack[2:4]
	repo.data = stack[4:13]
	repo.sat = stack[0:2]
	path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'+stack
	s = "Sentinel" + repo.level
	sats = Satelite.objects.filter(descricao=s)
	sat = None
	for s in sats:
		sat = s
	r = Raster.objects.get(pk=pk_indice)
	try:
		src_ref = rasterio.open(path + '/cortes/' + sat.bandReferencia + '.tif')
	except:
		return redirect('stack', pk, stack)
	raster = calc.indice_calc_formula(src_ref, sat, r.formula, path)
	calc.indice_write_tif(raster, src_ref, path + '/indices/', r.tag)

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
	classi = False
	paleta = utils.SEQ_COLOR_DEFAULT
	arq_id = None
	if menu=="Projeto":
		area = Area.objects.get(pk=pk)
		projeto = Projeto.objects.get(pk=area.projeto.pk)
		path = os.getcwd() + '/arquivos/projetos/' + projeto.pasta + '/' + area.pasta + '/' + stack + '/indices/'
		if (tipo=="Declividade"):
			path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'
			file = "declividade"
		if (tipo=="Altitude"):
			path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/'
			file = "altitude"
		if(tipo == "Mascara"):
			path = os.getcwd()+'/arquivos/projetos/'+projeto.pasta+'/'+area.pasta+'/mask/'
	if menu=="Modelo":
		area = AreaModelo.objects.get(pk=pk)
		modelo = Modelo.objects.get(pk=area.classe.modelo.pk)
		path_base = os.getcwd() + '/arquivos/modelos/' + modelo.pasta
		path = os.getcwd() + '/arquivos/modelos/' + modelo.pasta + '/'+str(area.pk)+'/'+stack+'/indices/'
		if (tipo == "Mascara"):
			path = path_base + '/masks/'
		if (tipo == "Declividade"):
			path = path_base + '/'+str(area.pk)+'/'
			file = "declividade"
		if (tipo == "Altitude"):
			path = path_base + '/'+str(area.pk)+'/'
			file = "altitude"
	if (tipo == "Mascara"):
		mask = path + str(area.pk) + ".geojson"
		with open(mask) as data_file:
			geoms = json.loads(data_file.read())
		obj = geoms['features'][0]['geometry']
		location = obj['coordinates'][0][0]
		m = folium.Map(
			location=[location[1], location[0]],
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
		if (tipo[:7] == 'Classi_'):
			classi = True
			arq_id = tipo[7:].split('*')[0]
			tipo = tipo[7:].split('*')[1]
			pasta = 'classificacao/'+arq_id+'/'
			path = path[:-8] + pasta
			paleta = utils.SEQ_GREY_SCALE_17
			div = 16
		if file =="":
			file = tipo
		src = rasterio.open(path+file+'.tif')
		min_n = 0.0
		src_saida = src.read()
		if (tipo == "Declividade" or tipo == "Altitude"):
			min_n = 0.0
		else:
			min_n = src_saida.min()
		location = utils.convertToWGS84(src)
		####Visualização no folium
		print("Visualização no folium...")
		m = folium.Map(
			location=[location[2], location[1]], 
			tiles='Stamen Terrain',
			#tiles="cartodbpositron",
			zoom_start=12
		)
		if classi:
			arq = ArquivoModelo.objects.get(pk=int(arq_id))
			modelo = arq.modelo
			classes = ClasseModelo.objects.filter(modelo=modelo)
			reds = []
			greens = []
			blues = []
			numeros = []
			i = 1
			for classe in classes:
				r, g, b= utils.hex_to_rgb(classe.cor)
				reds.append(r)
				greens.append(g)
				blues.append(b)
				numeros.append(i)
				i =i+1
			colors = pd.DataFrame()
			colors['num'] = numeros
			colors['r'] = reds
			colors['g'] = greens
			colors['b'] = blues
			colors = colors.set_index('num')
			utils.exportRGBAClasse(path, file, colors)
		else:
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

def mapateste_json(request, tag, sat='Sentinel2C'):
    #if not request.user.has_perm('aSocial.list_curso'):
        #raise PermissionDenied
    #### abrindo imagem
	erro = ""
	path = os.getcwd() + '/arquivos/testes/'+sat+'/'
	try:
		src = rasterio.open(path+tag+'.tif')
	except:
		erro = "A fórmula precisa ser testada primeiro!"
		return JsonResponse({'erro': erro})
	src_saida = src.read()
	location = utils.convertToWGS84(src)
	print("Visualização no folium...")
	m = folium.Map(
		location=[location[2], location[1]],
		tiles='Stamen Terrain',
		#tiles="cartodbpositron",
		zoom_start=15
	)
	min_n = src_saida.min()
	utils.exportRGBA(path, tag, min_n, src_saida.max())
	#add imagem do disco
	merc = os.path.join(path, tag+".png")
	if not os.path.isfile(merc):
		print(f"Could not find {merc}")
	else:
		imgR = folium.raster_layers.ImageOverlay(
			name=tag,
			image=merc,
			bounds=location[0],
			opacity=1,
		)
		#folium.Popup("I am an image").add_to(imgR)
		imgR.add_to(m)
		folium.LayerControl().add_to(m)
	m=m._repr_html_()

	return JsonResponse({'my_map_modal': m, 'erro':erro})
def summary_json(request, pk):
	arq = ArquivoModelo.objects.get(pk=pk)
	desc_arq = "Modelo: "+arq.modelo.descricao +" <br> Data de Treinamento: "+ str(arq.data_treinamento)
	imps = ImportanciaVariavel.objects.filter(arquivoModelo=arq)
	list = []
	list_imp = []
	for imp in imps:
		list_imp.append(imp.importancia)
		list.append(imp.variavel.variavel)
	return JsonResponse({'arq': arq.tipo.descricao, 'desc_arq': desc_arq, 'imp':list_imp, 'vars': list})

def dados_json(request, pk):
	modelo = Modelo.objects.get(pk=pk)
	desc_modelo = "Data Criação: "+str(modelo.data_criacao)
	classes = ClasseModelo.objects.filter(modelo = modelo)
	pie_y_class = []
	pie_y_data = []
	pie_test_data = []
	pie_total_data = []
	for cla in classes:
		pie_y_class.append(cla.classe)
		total = float(cla.total_dados)
		y = np.around(total*float(modelo.percent)/100.0)
		pie_y_data.append(y)
		pie_test_data.append(total - y)
		pie_total_data.append(total)
	pie_test_class = pie_y_class
	pie_total_class = pie_y_class
	return JsonResponse({'modelo': modelo.descricao,
						 'desc_modelo': desc_modelo,
						 'pie_total_class':pie_total_class,
						 'pie_total_data':pie_total_data,
						 'pie_test_class':pie_test_class,
						 'pie_test_data':pie_test_data,
						 'pie_y_class':pie_y_class,
						 'pie_y_data':pie_y_data
						}
	)