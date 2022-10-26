import sys, os, struct
import rasterio
from sklearn.linear_model import LinearRegression as lm
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier as rfc
from sklearn.datasets import make_classification
from sklearn.neural_network import MLPClassifier as rn
import joblib

def treinar_modelo(target, y, tipo, path):
	model_run = False
	model = None
	if tipo.tag == "rf":
		model = rfc(max_depth=2, random_state=0)
		model.fit(target, y)
		model_run = True
	if tipo.tag == "rn":
		model = rn(solver='lbfgs', alpha=1e-5,hidden_layer_sizes = (5, 2), random_state = 1)
		model.fit(target, y)
		model_run = True
	if tipo.tag == "svm":
		model = svm.SVC()
		model.fit(target, y)
		model_run = True
	filename = tipo.filename + '.sav'
	if model_run:
		joblib.dump(model, path+filename)

def modelo_linear(x, y):
	modelo = lm.fit(x, y)
	return modelo

def ler_modelo():
	os.environ["R_HOME"] = r"C:/Program Files/R/R-4.1.1"
	os.environ['R_USER'] = 'C:/Users/juan/Documents'
	import rpy2.robjects as robjects
	import rpy2.robjects.numpy2ri as numpy2ri
	from rpy2.robjects.conversion import localconverter
	from rpy2.robjects import r, pandas2ri 
	import anndata2ri
	from rpy2.robjects.packages import importr

	base = importr('base')
	utils = importr('utils')
	raster = importr('raster')
	predict = robjects.r['predict']
	values = robjects.r['values']
	numpy2ri.activate()
	pandas2ri.activate()
	anndata2ri.activate()
	readRDS = robjects.r['readRDS']
	df = readRDS(os.getcwd()+'\\modelos\\modelo_rf.rds')
	with localconverter(numpy2ri.converter):
		pandas_df_2_r = robjects.conversion.py2rpy(df)
	#df = robjects.conversion.py2rpy(df)
	raster_empilhado = empilhar()
	ras = robjects.conversion.py2rpy(raster_empilhado)
	predicao = predict(df, newdata = values(ras), filename="/modelos/teste.tif", type ="raw")
	predicao
	print(predicao)

def empilhar():
	ndvi = rasterio.open('projetos/AAA/Fazenda/2A1C20220402/indices/ndvi.tif')
	topo = rasterio.open('projetos/AAA/Fazenda/declividade.tif')
	band2_geo = ndvi.profile
	band2_geo.update({"count": 2})
	with rasterio.open('modelos/remp.tif', 'w', **band2_geo) as dest:
		dest.write(ndvi.read(1),1)
		dest.write(topo.read(1),2)
	src = rasterio.open('modelos/remp.tif')
	imgRio = src.read()
	return imgRio