# backend/core/admin.py
from django.contrib import admin
from .models import Profesor, Materia, Aula, Horario, Restriccion, SolicitudClase, VersionHorario

# Registra tus modelos aquí para que sean visibles y gestionables en el panel de administración
admin.site.register(Profesor)
admin.site.register(Materia)
admin.site.register(Aula)
admin.site.register(Horario)
admin.site.register(Restriccion)
admin.site.register(SolicitudClase)  # <-- Asegúrate de que esta línea esté
admin.site.register(VersionHorario)  # <-- Y esta también


# Opcional: Puedes personalizar cómo se muestran los modelos en el admin
# Por ejemplo:
# class ProfesorAdmin(admin.ModelAdmin):
#     list_display = ('nombre', 'email', 'especialidad', 'carga_horaria_maxima')
#     search_fields = ('nombre', 'email')
# admin.site.register(Profesor, ProfesorAdmin)
# Register your models here.
