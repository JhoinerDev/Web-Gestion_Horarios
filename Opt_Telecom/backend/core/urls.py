# backend/core/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfesorViewSet,
    MateriaViewSet,
    AulaViewSet,
    HorarioViewSet,
    RestriccionViewSet,
    ImportarHorariosExcelView,
    SolicitudClaseViewSet,
    VersionHorarioViewSet,
    AsignarSolicitudAHorarioView,
    GenerarHorariosView, # Confirmado que esta importación es correcta
    # Asegúrate de que las siguientes vistas también estén importadas si las necesitas,
    # ya que estaban en mi sugerencia anterior para completar el flujo:
    # ObtenerHorarioCompletoView,
    # ProcesarHorarioAlgoritmoView # Si GenerarHorariosView no es la misma
)

# Crear un enrutador para los ViewSets
router = DefaultRouter()
router.register('profesores', ProfesorViewSet)
router.register('materias', MateriaViewSet)
router.register('aulas', AulaViewSet)
router.register('horarios', HorarioViewSet)
router.register('restricciones', RestriccionViewSet)
router.register('solicitudes-clase', SolicitudClaseViewSet)
router.register('versiones-horario', VersionHorarioViewSet)

# Definir las URLs de la aplicación 'core'
urlpatterns = [
    # Incluye las URLs generadas automáticamente por el router para los ViewSets.
    path('', include(router.urls)),

    # Rutas para APIViews (que no son ViewSets) deben definirse explícitamente con path().

    # Ruta para la vista de importación de Excel.
    # Es una buena práctica usar un nombre de URL consistente, preferiblemente con guiones bajos.
    path('horarios/importar_excel/', ImportarHorariosExcelView.as_view(), name='importar_excel_horarios'),

    # Ruta para asignar una solicitud a un horario.
    # El <int:pk> permite que el ID de la solicitud sea parte de la URL.
    # El nombre de la ruta es claro.
    path('solicitudes-clase/<int:pk>/asignar_a_horario/', AsignarSolicitudAHorarioView.as_view(), name='asignar_solicitud_a_horario'),
    
    # Esta ruta 'prueba-post-excel/' parece redundante o para un propósito específico de testing.
    # Si 'importar_excel_horarios' ya es el endpoint para subir el excel, considera eliminar esta.
    # Si es para un tipo diferente de importación, renómbrala para mayor claridad.
    # path('prueba-post-excel/', ImportarHorariosExcelView.as_view(), name='prueba_post_excel'),
    # => Recomendación: Eliminar si 'importar_excel_horarios' es suficiente, o renombrar.

    # Ruta para generar/procesar los horarios con el algoritmo.
    # El nombre 'generar_horarios' es claro.
    path('generar-horarios/', GenerarHorariosView.as_view(), name='generar_horarios'),
    path('importar-horarios-excel/', ImportarHorariosExcelView.as_view(), name='importar_horarios_excel'),


    # === Sugerencias adicionales (si las necesitas en tu flujo) ===
    # Si necesitas una vista para obtener el "horario completo" actual (no una versión guardada),
    # podrías añadirla aquí. Asumo que GenerarHorariosView devuelve el horario generado.
    # path('horario-actual/', ObtenerHorarioActualView.as_view(), name='obtener_horario_actual'),

    # Si tu GenerarHorariosView solo dispara el proceso y necesitas otro endpoint
    # para consultar el estado o resultado del algoritmo.
    # path('estado-generacion-horarios/', EstadoGeneracionHorariosView.as_view(), name='estado_generacion_horarios'),
]