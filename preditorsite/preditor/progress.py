from .models import Projeto, BarraProgresso
from django.http import HttpResponse,JsonResponse
from django.utils import timezone
##### PROGRESS
def progress(request):
	progressos = BarraProgresso.objects.filter(hash=request.session.get('hash_progress'))
	jason ={'data':'0', 'text': 'iniciando...'}
	if progressos:
		progresso = progressos[len(progressos)-1]
		jason['data'] = progresso.percent
		jason['text'] = progresso.mov
	print(jason)
	return JsonResponse(jason) 

def progress_create(projeto, processo, request):
	progresso = BarraProgresso()
	progresso.usuario = request.user
	progresso.data_criacao = timezone.now()
	progresso.projeto = projeto
	progresso.processo = processo
	progresso.hash = request.session.get('hash_progress')
	progresso.percent = 0
	progresso.mov = 'Iniciando ...'
	progresso.save()
	return progresso

def progress_save(percent, mov, progresso):
	progresso.mov = mov
	progresso.percent = percent
	if percent == 100:
		progresso.data_finalizacao = timezone.now()
	progresso.save()