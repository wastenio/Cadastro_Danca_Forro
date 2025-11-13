from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Participant
from django.utils.html import format_html
from django.urls import reverse

# Define o recurso de importação/exportação
class ParticipantResource(resources.ModelResource):
    class Meta:
        model = Participant
        fields = ('id', 'name', 'email', 'created_at', 'checked_in')
        export_order = ('id', 'name', 'email', 'created_at', 'checked_in')

@admin.register(Participant)
class ParticipantAdmin(ImportExportModelAdmin):
    resource_class = ParticipantResource
    list_display = ('name', 'email', 'phone', 'created_at', 'checked_in')
    readonly_fields = ('uuid', 'qr_code', 'created_at', 'checked_in_at')
    search_fields = ('name', 'email')
    list_filter = ('checked_in',)
    
    def delete_button(self, obj):
        url = reverse('admin:participants_participant_delete', args=[obj.pk])
        return format_html(f'<a class="button" href="{url}" style="color:red;">🗑️ Excluir</a>')
    delete_button.short_description = 'Ações'