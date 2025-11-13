from django.shortcuts import render, redirect, get_object_or_404
from .forms import ParticipantForm
from .models import Participant
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.utils import timezone


def register(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.save()

            # 🔹 1. Gerar o QR Code com a URL contendo o UUID
            qr_data = request.build_absolute_uri(f"/participants/checkin/{participant.uuid}/")
            img = qrcode.make(qr_data)

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filebuffer = ContentFile(buffer.getvalue())

            # 🔹 2. Salvar o QR Code no modelo
            participant.qr_code.save(f'{participant.uuid}.png', filebuffer)
            participant.save()

            # 🔹 3. Enviar e-mail com QR Code
            email_subject = 'Confirmação de Inscrição - Evento'
            email_body = f"""
            Olá {participant.name},

            Sua inscrição foi confirmada com sucesso! 
            Apresente o QR Code em anexo no dia do evento para realizar seu check-in.

            Atenciosamente,
            Equipe do Evento
            """
            email = EmailMessage(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [participant.email],
            )
            email.attach(f'{participant.uuid}.png', buffer.getvalue(), 'image/png')

            try:
                email.send(fail_silently=False)
            except Exception as e:
                print("❌ Erro ao enviar o e-mail:", e)

            # 🔹 4. Redirecionar para a página de sucesso
            return redirect(f"{reverse('register')}?success=1")
        else:
            return render(request, 'register.html', {'form': form, 'errors': form.errors})

    else:
        form = ParticipantForm()
        success = request.GET.get('success') == '1'
        return render(request, 'register.html', {'form': form, 'success': success})
    
def checkin_by_uuid(request, uuid):
    participant = get_object_or_404(Participant, uuid=uuid)
    message = None
    if participant.checked_in:
        message = {'status': 'already', 'text': f"{participant.name} já fez check-in em {participant.checked_in_at}."}
    else:
        participant.checked_in = True
        participant.checked_in_at = timezone.now()
        participant.save()
        message = {'status': 'ok', 'text': f"Check-in efetuado para {participant.name}."}


    return render(request, 'checkin_result.html', {'participant': participant, 'message': message})

def validate_qr(request, uuid):
    try:
        participant = Participant.objects.get(uuid=uuid)
        data = {
            'valid': True,
            'name': participant.name,
            'checked_in': participant.checked_in,
            'checked_in_at': participant.checked_in_at,
        }
    except Participant.DoesNotExist:
        data = {'valid': False}

    # ✅ Se quiser exibir no navegador:
    if request.GET.get('html'):
        return render(request, 'checkin.html', {'data': data})

    # ✅ Se quiser usar via leitor ou app (JSON):
    return JsonResponse(data)
