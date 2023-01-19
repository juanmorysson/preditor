from django import forms
from .models import Projeto, Area, Modelo, AreaModelo, ClasseModelo, Raster, Satelite, VariavelModelo
import datetime

class ModeloForm(forms.ModelForm):

    class Meta:
        model = Modelo
        fields = ( 'descricao', )

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }

class VariavelModeloForm(forms.ModelForm):
    class Meta:
        model = VariavelModelo
        fields = ( 'variavel', )

        widgets = {
            'variavel': forms.TextInput(attrs={'class': 'form-control'}),
        }

class IndiceForm(forms.ModelForm):

    class Meta:
        model = Raster
        fields = ( 'tag','formula','satelite', )
        labels = {'satelite':'Sensor' }
        widgets = {
            'tag': forms.TextInput(attrs={'class': 'form-control'}),
            'formula': forms.TextInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, user, *args, **kwargs):
        super(IndiceForm, self).__init__(*args, **kwargs)
        sensores = Satelite.objects.filter(publica=True)
        list = []
        s_resp = Satelite.objects.filter(responsavel=user)
        for ss in sensores:
            item = (ss.pk, ss.descricao)
            list.append(item)
        for s in s_resp:
            item = (s.pk, s.descricao)
            list.append(item)
        self.fields['satelite'].choices = list
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
        fields = ( 'descricao',)

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),

        }

class AreaForm(forms.ModelForm):

    class Meta:
        model = Area
        fields = ('descricao', )

        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),

        }
