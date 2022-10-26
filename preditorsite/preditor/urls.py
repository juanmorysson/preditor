from django.urls import path, include
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.index, name="index"),
    path('user', views.user, name='user'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('logout', LogoutView.as_view()),
    
    path('progress', views.progress.progress, name='progress' ),
    path('progressos', views.progressos, name='progressos' ),
    path('unzip/<ar>/', views.utils.unzip, name='unzip'),
    
    path('draw2', views.draw, name="draw"),
    path('clear_projeto_sessao', views.clear_projeto_sessao, name="clear_projeto_sessao"),

    path('modelos', views.modelos, name="modelos"),
    path('modelo/<int:pk>/', views.modelo_open, name='modelo_open'),
    path('modelo/new', views.modelo_new, name='modelo_new'),
    path('modelo/gerar_stacks/<int:pk>/', views.gerar_stacks_modelo, name='gerar_stacks_modelo'),
    path('modelo/ver_stacks/<int:pk>/', views.ver_stacks_modelo, name='ver_stacks_modelo'),
    path('modelo/<int:pk>/edit/', views.modelo_edit, name='modelo_edit'),
    path('modelo/prepararDF/<int:pk>', views.prepararDataFrameModelo_Request, name='prepararDataFrameModelo_Request'),
    path('modelo/treinar/<int:pk>', views.treinar_Request, name='treinar_Request'),

    path('classe_modelo/new/<int:pk>/', views.classe_modelo_new, name='classe_modelo_new'),
    path('classe_modelo/<int:pk>/', views.classe_modelo_edit, name='classe_modelo_edit'),
    path('area_modelo/new/<int:pk>/', views.area_modelo_new, name='area_modelo_new'),
    path('area_modelo/<int:pk>/', views.area_modelo_edit, name='area_modelo_edit'),
    path('area_modelo/uploadMask/<int:pk>/', views.uploadMaskModelo, name="uploadMaskModelo"),
    path('area_modelo/uploadPoints/<int:pk>/', views.uploadPointsModelo, name="uploadPointsModelo"),
    

    path('projetos', views.projetos, name="projetos"),
    path('projeto/<int:pk>/', views.projeto_open, name='projeto_open'),
    path('projeto/new', views.projeto_new, name='projeto_new'),
    path('area/new', views.area_new, name='area_new'),
    path('area/<int:pk>/', views.area_open, name="area_open"),
    path('area/uploadMask/<int:pk>/', views.uploadMask, name="uploadMask"),
    path('area/uploadPoints/<int:pk>/', views.uploadPoints, name="uploadPoints"),
    path('area/gerar_indices/<int:pk>/<stack>', views.gerar_indices_area, name="gerar_indices_area"),
    path('area/gerar_indice/<int:pk>/<stack>/<pk_indice>', views.gerar_indice_area, name="gerar_indice_area"),
    path('stack/<int:pk>/<stack>', views.stack, name="stack"),
    path('declividade/gerar/<int:pk>/', views.declividade_gerar, name="declividade_gerar"),
    path('declividade/<int:pk>/', views.declividade, name="declividade"),
    path('altitude/gerar/<int:pk>/', views.altitude_gerar, name="altitude_gerar"),
    path('altitude/<int:pk>/', views.altitude, name="altitude"),

    path('download', views.download_sentinel, name="download_sentinel"),
    path('download_page', views.download_page, name="download_page"),
    path('trescores', views.trescores, name="trescores"),
    path('trescores_page', views.trescores_page, name="trescores_page"),
    path('ndvi', views.ndvi, name="ndvi"),
    path('ndvi/<int:pk>/<stack>', views.ndvi, name="ndvi"),
    #path('ndviee', views.ndviee, name="ndviee"),
    path('ndvi_page', views.ndvi_page, name="ndvi_page"),
    path('histograma', views.histograma, name="histograma"),
    path('cortar_page', views.cortar_page, name="cortar_page"),
    path('cortar', views.cortar, name="cortar"),
    path('cortar/<int:pk>/<stack>', views.cortar, name="cortar"),

    path('mapa_json/<pk>/<stack>/<tipo>/<menu>', views.mapa_json, name='mapa_json' ),
]