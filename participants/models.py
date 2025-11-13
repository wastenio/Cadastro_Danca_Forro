from django.db import models
import uuid
from django.utils import timezone




def qr_image_path(instance, filename):
    # salva em media/qrcodes/<uuid>.png
    return f'qrcodes/{instance.uuid}.png'


class Participant(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(blank=True, null=True)
    qr_code = models.ImageField(upload_to=qr_image_path, blank=True, null=True)


    def __str__(self):
        return f"{self.name} ({self.uuid})"