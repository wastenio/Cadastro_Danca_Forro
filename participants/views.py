import base64
import qrcode
import requests

from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.files.base import ContentFile

from .forms import ParticipantForm
from .models import Participant


MAILTRAP_API_TOKEN = "df5a16d40af66da836b740db864152d4"
MAILTRAP_API_URL = "https://send.api.mailtrap.io/api/send"


def register(request):
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

                    # Converter QR para base64 (API exige isso)
                    qr_base64 = base64.b64encode(buffer_email.getvalue()).decode()

            except IntegrityError:
                form.add_error('email', 'Já existe um participante cadastrado com esse e-mail.')
                return render(request, 'register.html', {
                    'form': form,
                    'errors': form.errors,
                    'success': False
                })

            # ========= ENVIO VIA MAILTRAP API HTTP ========= #

            payload = {
                "from": {
                    "email": "no-reply@novembroazul.com.br",
                    "name": "Evento Novembro Azul"
                },
                "to": [
                    {"email": participant.email}
                ],
                "subject": "Confirmação de Inscrição - Novembro Azul",
                "text": (
                    f"Olá {participant.name},\n\n"
                    "Sua inscrição no evento Novembro Azul foi confirmada!\n"
                    "Apresente o QR Code em anexo na entrada.\n\n"
                    "Atenciosamente,\nEquipe do Evento"
                ),
                "attachments": [
                    {
                        "filename": f"{participant.uuid}.png",
                        "content": qr_base64,
                        "type": "image/png"
                    }
                ]
            }

            headers = {
                "Authorization": f"Bearer {MAILTRAP_API_TOKEN}",
                "Content-Type": "application/json"
            }

            response = requests.post(MAILTRAP_API_URL, json=payload, headers=headers)

            # Checar envio
            if response.status_code not in [200, 202]:
                return render(request, "register.html", {
                    "form": form,
                    "errors": {"email": "Erro ao enviar e-mail. Tente novamente."},
                    "success": False
                })

            return redirect(f"{reverse('participants:register')}?success=1")

        else:
            return render(request, 'register.html', {
                'form': form,
                'errors': form.errors,
                'success': False
            })

    # GET
    form = ParticipantForm()
    success = request.GET.get('success') == '1'

    return render(request, 'register.html', {
        'form': form,
        'success': success,
        'errors': None
    })


def checkin_by_uuid(request, uuid):
    participant = get_object_or_404(Participant, uuid=uuid)

    if participant.checked_in:
        message = {
            "status": "already",
            "text": f"{participant.name} já fez check-in em {participant.checked_in_at}."
        }
    else:
        participant.checked_in = True
        participant.checked_in_at = timezone.now()
        participant.save()
        message = {
            "status": "ok",
            "text": f"Check-in efetuado para {participant.name}."
        }

    return render(request, "checkin_result.html", {
        "participant": participant,
        "message": message
    })


def validate_qr(request, uuid):
    try:
        participant = Participant.objects.get(uuid=uuid)
        data = {
            "valid": True,
            "name": participant.name,
            "checked_in": participant.checked_in,
            "checked_in_at": participant.checked_in_at,
        }
    except Participant.DoesNotExist:
        data = {"valid": False}

    if request.GET.get("html"):
        return render(request, "checkin.html", {"data": data})

    return JsonResponse(data)
