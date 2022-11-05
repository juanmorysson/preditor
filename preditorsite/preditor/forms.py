from django import forms
from .models import Projeto, Area, Modelo, AreaModelo, ClasseModelo, Raster
import datetime

class ModeloForm(forms.ModelForm):

    class Meta:
        model = Modelo
        fields = ( 'descricao','pasta', )

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'pasta': forms.TextInput(attrs={'class': 'form-control'}),
        }

class IndiceForm(forms.ModelForm):

    class Meta:
        model = Raster
        fields = ( 'tag','formula', )
        labels = {'tag': 'Índice', }

        widgets = {
            'tag': forms.TextInput(attrs={'class': 'form-control'}),
            'formula': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ClasseModeloForm(forms.ModelForm):

    class Meta:
        model = ClasseModelo
        fields = ( 'classe','cor', )

        widgets = {
            'classe': forms.TextInput(attrs={'class': 'form-control'}),
            'cor': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
        }

class AreaModeloForm(forms.ModelForm):

    class Meta:
        model = AreaModelo
        fields = ( 'descricao', )

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, pk, *args, **kwargs):
        #pk = kwargs.get('pk')
        modelo = Modelo.objects.get(pk=pk)
        super(AreaModeloForm, self).__init__(*args, **kwargs)
        self.fields['Classe']=forms.ModelChoiceField(queryset=ClasseModelo.objects.filter(modelo=modelo))

class ProjetoForm(forms.ModelForm):

    class Meta:
        model = Projeto
        fields = ( 'descricao','pasta', )

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'pasta': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AreaForm(forms.ModelForm):

    class Meta:
        model = Area
        fields = ('descricao','pasta', )

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'pasta': forms.TextInput(attrs={'class': 'form-control'}),
        }
