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
from django.urls import reverse
from django.db import transaction, IntegrityError


def register(request):
    success = False
    errors = None

    if request.method == 'POST':
        form = ParticipantForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Salvar participante
                    participant = form.save(commit=False)
                    participant.save()

                    # --------- GERAR QR CODE ---------
                    qr_data = request.build_absolute_uri(
                        f"/participants/checkin/{participant.uuid}/"
                    )
                    img = qrcode.make(qr_data)

                    # Buffer para salvar no modelo
                    buffer_model = BytesIO()
                    img.save(buffer_model, format='PNG')
                    participant.qr_code.save(
                        f"{participant.uuid}.png",
                        ContentFile(buffer_model.getvalue())
                    )

                    # Buffer separado para o email
                    buffer_email = BytesIO()
                    img.save(buffer_email, format='PNG')

            except IntegrityError:
                form.add_error('email', 'Já existe um participante cadastrado com esse e-mail.')
                return render(request, 'register.html', {
                    'form': form,
                    'errors': form.errors,
                    'success': False
                })

            # --------- ENVIAR EMAIL ---------
            email_subject = 'Confirmação de Inscrição - Evento'
            email_body = (
                f"Olá {participant.name},\n\n"
                "Sua inscrição foi confirmada!\n"
                "O QR Code para entrada está em anexo.\n\n"
                "Até o evento!"
            )

            email = EmailMessage(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [participant.email],
            )

            email.attach(
                f'{participant.uuid}.png',
                buffer_email.getvalue(),
                'image/png'
            )

            email.send(fail_silently=False)

            # Redirecionar para evitar reenvio acidental do formulário
            return redirect(f"{reverse('participants:register')}?success=1")

        else:
            # Form inválido
            return render(request, 'register.html', {
                'form': form,
                'errors': form.errors,
                'success': False
            })

    # ---------- MÉTODO GET ----------
    else:
        form = ParticipantForm()
        success = request.GET.get('success') == '1'

        return render(request, 'register.html', {
            'form': form,
            'success': success,
            'errors': None
        })

    
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
