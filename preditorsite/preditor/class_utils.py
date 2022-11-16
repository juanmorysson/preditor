##########   Classes Apoio  ##############

class Arquivo():
	desc = ""
	tipo = ""

	def __init__(self, desc, tipo):
		self.desc = desc
		self.tipo = tipo

	def __str__(self):
		return self.desc + "T: "+self.tipo

class RepoSentinel():
	data = ""
	data_format = ""
	level = ""
	sat = ""
	tile = ""
	marked = False

	def __str__(self):
		return self.level + " - Data: "+self.data

class Variavel():
	id
	tag = ""
	marked = False

	def __init__(self, id, tag, marked):
		self.id = id
		self.tag = tag
		self.marked = marked

class AreaList():
	id
	area = ""
	lista = []

	def __init__(self, id, area, lista):
		self.id = id
		self.area = area
		self.lista = lista