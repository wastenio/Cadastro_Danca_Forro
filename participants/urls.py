from django.urls import path
from . import views


app_name = 'participants'


urlpatterns = [
    path('register/', views.register, name='register'),
    path('checkin/<uuid:uuid>/', views.checkin_by_uuid, name='checkin'),
    path('validate/<uuid:uuid>/', views.validate_qr, name='validate'),
]