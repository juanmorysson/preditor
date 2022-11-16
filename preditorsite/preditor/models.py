from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Modelo(models.Model):
    pasta = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=200)
    responsavel = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    data_criacao =  models.DateTimeField(null=True,blank=True)
    stack = models.CharField(max_length=200, null=True)
    percent = models.CharField(max_length=3, null=True)
    upload = models.BooleanField(default=False)

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
    data_treinamento = models.DateTimeField(null=True, blank=True)
    loop_cross = models.CharField(max_length=20, null=True)
    max_depth = models.CharField(max_length=20, null=True)
    acuraciaTreinoMedia = models.CharField(max_length=20, null=True)
    acuraciaTreinoMaior = models.CharField(max_length=20, null=True)
    acuraciaTreinoMenor = models.CharField(max_length=20, null=True)
    data_teste = models.DateTimeField(null=True, blank=True)
    acuraciaTeste = models.CharField(max_length=20, null=True)

class ImportanciaVariavel(models.Model):
    arquivoModelo = models.ForeignKey(ArquivoModelo, on_delete=models.CASCADE, null=False)
    variavel = models.CharField(max_length=20, null=True)
    importancia = models.CharField(max_length=20, null=True)

class ClasseModelo(models.Model):
    classe = models.CharField(max_length=200, null=False, blank=False)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=False)
    cor = models.CharField(max_length=8, null=False, blank=False)

    def __str__(self):
        return self.classe

class AreaModelo(models.Model):
    descricao = models.CharField(max_length=200, null=True)
    classe = models.ForeignKey(ClasseModelo, on_delete=models.CASCADE, null=False)

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
class Raster(models.Model):
    tag = models.CharField(max_length=200, unique=True)
    isIndex = models.BooleanField(default=False)
    formula = models.CharField(max_length=200, null=True, blank=True)
    responsavel = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    publica = models.BooleanField(default=False)
    def __str__(self):
        return self.tag
class Raster_Modelo(models.Model):
    raster = models.ForeignKey(Raster, on_delete=models.CASCADE, null=False)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=False)
    data_criacao = models.DateTimeField(default=timezone.now)
class Satelite(models.Model):
    descricao = models.CharField(max_length=200)
    bandReferencia = models.CharField(max_length=200)
    def __str__(self):
        return self.descricao

class RasterBand(models.Model):
    band = models.CharField(max_length=200)
    tagOnSat = models.CharField(max_length=200)
    raster = models.ForeignKey(Raster, on_delete=models.CASCADE, null=False)
    satelite = models.ForeignKey(Satelite, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return self.satelite.descricao + " - " + self.band + " - " +  self.tagOnSat + " - " +  self.raster.tag

class BarraProgresso(models.Model):
    percent = models.CharField(max_length=2)
    processo = models.CharField(max_length=10)
    mov = models.CharField(max_length=500)
    hash = models.CharField(max_length=500)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, null=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    data_criacao =  models.DateTimeField(null=True,blank=True)
    data_finalizacao =  models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.percent


# Create your models here.
