from django.contrib import admin

from .models import Raster,  RasterBand, Satelite

admin.site.register(Raster)
admin.site.register(RasterBand)
admin.site.register(Satelite)
