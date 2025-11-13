from django.urls import path
from . import views
from django.views.generic import RedirectView


app_name = 'participants'


urlpatterns = [
    path('register/', views.register, name='register'),
    path('checkin/<uuid:uuid>/', views.checkin_by_uuid, name='checkin'),
    path('validate/<uuid:uuid>/', views.validate_qr, name='validate'),
    
    path('', RedirectView.as_view(url='register/', permanent=False)),
]