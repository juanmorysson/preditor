from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Satelite(models.Model):
    descricao = models.CharField(max_length=200)
    bandReferencia = models.CharField(max_length=200)
    responsavel = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    publica = models.BooleanField(default=False)
    bandas = models.IntegerField(default=0)
    def __str__(self):
        return self.descricao
class Modelo(models.Model):
    pasta = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=200)
    responsavel = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    data_criacao =  models.DateTimeField(null=True,blank=True)
    stack = models.CharField(max_length=200, null=True)
    percent = models.CharField(max_length=3, null=True)
    total_dados = models.CharField(max_length=200, null=True)
    upload = models.BooleanField(default=False)
    sensor = models.ForeignKey(Satelite, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.descricao

class TipoArquivoModelo(models.Model):
    tag = models.CharField(max_length=50)
    filename = models.CharField(max_length=50)
    descricao = models.CharField(max_length=50)
    def __str__(self):
        return self.descricao
class ArquivoModelo(models.Model):
    tipo = models.ForeignKey(TipoArquivoModelo, on_delete=models.CASCADE, null=True)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=False)
    data_inicio_treinamento = models.DateTimeField(null=True, blank=True)
    data_treinamento = models.DateTimeField(null=True, blank=True)
    data_validacao = models.DateTimeField(null=True, blank=True)
    loop_cross = models.CharField(max_length=20, null=True)
    max_depth = models.CharField(max_length=20, null=True)
    n_estimators = models.CharField(max_length=20, null=True)
    kernel = models.CharField(max_length=20, null=True)
    acuraciaTreinoMedia = models.CharField(max_length=20, null=True)
    acuraciaTreinoMaior = models.CharField(max_length=20, null=True)
    acuraciaTreinoMenor = models.CharField(max_length=20, null=True)
    data_teste = models.DateTimeField(null=True, blank=True)
    acuraciaTeste = models.CharField(max_length=20, null=True)

    @property
    def tempotreino(self):
        tempo = "00"
        try:
            tempo = abs((self.data_treinamento - self.data_inicio_treinamento).seconds)
        except:
            print(tempo)
        return tempo
    @property
    def tempovalidacao(self):
        tempo = "00"
        try:
            tempo = abs((self.data_validacao - self.data_treinamento).seconds)
        except:
            tempo = "00"
        return tempo

class VariavelModelo(models.Model):
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=False)
    variavel = models.CharField(max_length=20, null=True)

class ImportanciaVariavel(models.Model):
    arquivoModelo = models.ForeignKey(ArquivoModelo, on_delete=models.CASCADE, null=False)
    variavel = models.ForeignKey(VariavelModelo, on_delete=models.CASCADE, null=True)
    importancia = models.CharField(max_length=20, null=True)


class ClasseModelo(models.Model):
    classe = models.CharField(max_length=14, null=False, blank=False)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=False)
    cor = models.CharField(max_length=8, null=False, blank=False)
    total_dados = models.CharField(max_length=200, null=True, default="0")

    def __str__(self):
        return self.classe

class AreaModelo(models.Model):
    descricao = models.CharField(max_length=200, null=True)
    classe = models.ForeignKey(ClasseModelo, on_delete=models.CASCADE, null=False)
    tamanho = models.CharField(max_length=200, null=True)
    def __str__(self):
        return self.descricao

class Projeto(models.Model):
    pasta = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=200)
    responsavel = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    data_criacao = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.descricao

class Area(models.Model):
    pasta = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=200)
    responsavel = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    data_criacao =  models.DateTimeField(null=True,blank=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.descricao

class DadosClassificacao(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True)
    arquivoModelo = models.ForeignKey(ArquivoModelo, on_delete=models.CASCADE, null=True)
    stack = models.CharField(max_length=200, null=True)
    classe = models.CharField(max_length=200, null=True)
    quantidade = models.CharField(max_length=200, null=True)

class Raster(models.Model):
    tag = models.CharField(max_length=200, unique=False)
    band = models.CharField(max_length=200, null=True, blank=True)
    tagOnSat = models.CharField(max_length=200, null=True, blank=True)
    satelite = models.ForeignKey(Satelite, on_delete=models.CASCADE, null=True)
    isIndex = models.BooleanField(default=False)
    formula = models.CharField(max_length=200, null=True, blank=True)
    responsavel = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    publica = models.BooleanField(default=False)
    def __str__(self):
        return self.satelite.descricao+ ": "+self.tag +" - "+ verificaBool(self.isIndex,"Índice","Banda")

def verificaBool(b, v, f):
	if b:
		return v
	else:
		return f
class Raster_Modelo(models.Model):
    raster = models.ForeignKey(Raster, on_delete=models.CASCADE, null=False)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=False)
    data_criacao = models.DateTimeField(default=timezone.now)

class BarraProgresso(models.Model):
    percent = models.CharField(max_length=2)
    processo = models.CharField(max_length=10)
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    data_criacao =  models.DateTimeField(null=True,blank=True)
    data_finalizacao =  models.DateTimeField(null=True,blank=True)
    ativo = models.BooleanField(default=True)
    mov = models.CharField(max_length=400, null=True)

    def __str__(self):
        return self.percent

    def movi(self, percent, mov):
        self.mov = mov
        self.percent = percent

    def finalizar(self):
        self.data_finalizacao = timezone.now()
        self.percent = "100"
        self.mov = "Finalizado"
        self.ativo = False

    def cancelar(self):
        self.data_finalizacao = timezone.now()
        self.mov = "Cancelado pelo usuário"
        self.ativo = False

        # Create your models here.
