from django.contrib import admin

from .models import Raster,  Satelite, ArquivoModelo, TipoArquivoModelo

admin.site.register(Raster)
admin.site.register(Satelite)
admin.site.register(TipoArquivoModelo)
