import sys, os, struct
import rasterio
from sklearn.linear_model import LinearRegression as lm
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier as rfc
from sklearn.model_selection import KFold
from sklearn.datasets import make_classification
from sklearn.model_selection import cross_val_score
from sklearn.inspection import permutation_importance
import joblib

def testar_modelo(model, X_test, Y_test):
	result = model.score(X_test, Y_test)
	return result

def classificar(model, df_dados_stack):
	return model.predict(df_dados_stack)

def validar_modelo(model, target, y, split_cross):
	print("Verificando results")
	cv = KFold(n_splits=split_cross, shuffle=True)
	results = cross_val_score(model, target, y, cv=cv)
	mean = results.mean()
	max = results.max()
	min = results.min()
	menor = "%.5f" % (min * 100)
	maior = "%.5f" % (max * 100)
	mean = "%.5f" % (mean * 100)
	return mean, menor, maior
def treinar_modelo(target, y, tipo, max_depth, list_cols = None):
	model = None
	importance = None
	if tipo.tag == "rf":
		model = rfc(max_depth=max_depth, random_state=0)
		model.fit(target, y)
		model.feature_names_in_= list_cols
		print("Verificando importâncias")
		results = permutation_importance(model, target, y, scoring='accuracy')
		importance = results.importances_mean
		#results = permutation_importance(model, target, y, scoring='accuracy')
		#importance = results.importances_mean
		#for i, v in enumerate(importance):
		#	print('Feature: %0d, Score: %.5f' % (i, v))
	if tipo.tag == "svm":
		model = svm.SVC()
		model.fit(target, y)
		print("Verificando importâncias")
		if model.kernel == "rbf":
			importance = permutation_importance(model, target, y)
		if model.kernel == "linear":
			importance = model.coef_

	return model, importance

def ler_modelo_arquivo(arq):
	path = os.getcwd() +"/arquivos/modelos/"+arq.modelo.pasta+"/modelos/"
	filename = ""
	try:
		filename = arq.tipo.filename
	except:
		print("não há tipo arquivo")
	model = joblib.load(open(path+filename+str(arq.id) +".sav", 'rb'))
	if str(model)=="SVC()":
		print("SVM")
	if str(model)[:22] == "RandomForestClassifier":
		print("RF")
		#print(model.coefs_)
	return model

def ler_modelo_up(file):
	model = joblib.load(file)
	try:
		print(model.feature_names_in_)
	except:
		print("não deu")
	if str(model) == "SVC()":
		print("SVM")
	if str(model)[:22] == "RandomForestClassifier":
		print("RF")
	return model

# print(model.coefs_)
#testar
	#result = loaded_model.score(X_test, Y_test)


#### LIXO - exemplos
def modelo_linear(x, y):
	modelo = lm.fit(x, y)
	return modelo

def ler_modelo_R():
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
	df = readRDS(os.getcwd()+'/modelos/modelo_rf.rds')
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

