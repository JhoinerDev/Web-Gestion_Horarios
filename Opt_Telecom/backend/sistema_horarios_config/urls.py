# backend/sistema_horarios_config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta única línea incluye TODAS las rutas definidas en core.urls
    # bajo el prefijo '/api/'. Por ejemplo:
    # - /api/profesores/
    # - /api/materias/
    # - /api/horarios/
    # - /api/solicitudes-clase/
    # - /api/versiones-horario/
    # - /api/horarios/importar_excel/
    # - /api/solicitudes-clase/<pk>/asignar_a_horario/
    path('api/', include('core.urls')), 
]