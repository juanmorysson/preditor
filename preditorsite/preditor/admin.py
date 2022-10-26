from django.contrib import admin

from .models import Raster,  RasterBand, Satelite, ArquivoModelo, TipoArquivoModelo

admin.site.register(Raster)
admin.site.register(RasterBand)
admin.site.register(Satelite)
admin.site.register(TipoArquivoModelo)
