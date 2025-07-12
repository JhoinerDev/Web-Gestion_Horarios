# backend/core/models.py

from django.db import models
from django.db.models import JSONField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import json

# --- Funciones de validación para JSONField ---
# Esta función es un validador básico para asegurar que el contenido sea un JSON válido.
# Es buena práctica tenerla, aunque JSONField de Django ya maneja algo de esto.
def validate_json_schema(value):
    try:
        # Intenta serializar el valor para confirmar que es un JSON válido.
        # Si 'value' ya es un dict/list, json.dumps lo convertirá a string.
        # Si no es un tipo serializable, lanzará TypeError.
        # Se puede mejorar la validación para tipos específicos si es necesario.
        json.dumps(value) 
    except TypeError:
        raise ValidationError(
            _('%(value)s no es una estructura JSON válida.'),
            params={'value': value},
        )

# --- Tus modelos existentes ---
class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=200, blank=True, null=True) # Puede ser opcional
    carga_horaria_maxima = models.IntegerField(default=0, help_text="Máximo de horas semanales que el profesor puede impartir.")
    # JSONField para almacenar la disponibilidad horaria del profesor
    # Ejemplo: {"LUN": ["08:00-12:00", "14:00-18:00"], "MAR": ["09:00-13:00"]}
    # Importante: default=dict para que los nuevos objetos tengan un diccionario vacío por defecto.
    disponibilidad = models.JSONField(default=dict, blank=True, null=True, help_text="Disponibilidad horaria del profesor por día de la semana en formato JSON. Ej: {'LUN': ['08:00-12:00']}") 
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    categoria = models.CharField(max_length=50, null=True, blank=True) 
    regimen = models.CharField(max_length=50, null=True, blank=True) 
    dedicatoria = models.CharField(max_length=50, null=True, blank=True) 
    carrera_principal = models.CharField(max_length=100, null=True, blank=True, help_text="Carrera principal a la que está adscrito el profesor.")

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        verbose_name_plural = "Profesores"
        # Mantener unique_together para nombre y apellido, pero considera la cédula como el más único
        unique_together = ('nombre', 'apellido') # Añadido para prevenir duplicados, aunque cedula es más robusta

class Aula(models.Model):
    codigo = models.CharField(max_length=50, unique=True, help_text="Código identificador único para el aula.")
    tipo = models.CharField(
        max_length=50, 
        help_text="Ej: 'Teórica', 'Laboratorio', 'Seminario', 'Salón de Clases'",
        default='Salón de Clases' 
    )
    capacidad = models.IntegerField(help_text="Número máximo de estudiantes que el aula puede albergar.")
    ubicacion = models.CharField(max_length=100, blank=True, null=True, help_text="Ubicación física del aula (ej. Edificio A, Piso 3).")
    # JSONField para almacenar una lista de recursos especiales del aula
    # Ejemplo: ["Proyector", "Pizarra Interactiva", "Computadoras"]
    recursos_especiales = models.JSONField(default=list, blank=True, null=True, help_text="Lista de recursos adicionales del aula en formato JSON. Ej: ['Proyector', 'Pizarra Interactiva']") 

    def __str__(self):
        return self.codigo
    
    class Meta:
        verbose_name_plural = "Aulas"

class Materia(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre de la materia.")
    horas_semanales = models.IntegerField(default=0, help_text="Total de horas que la materia debe impartirse a la semana (incluye teoría, práctica, laboratorio).")
    horas_teoricas = models.IntegerField(default=0, help_text="Horas de teoría por semana para esta materia.")
    horarios_de_practicas = models.IntegerField(default=0, help_text="Horas de práctica por semana para esta materia.") 
    horario_de_laboratorio = models.IntegerField(default=0, help_text="Horas de laboratorio por semana para esta materia.")
    tipo_de_materia = models.CharField(max_length=50, default='Obligatoria', help_text="Tipo de materia (ej. Obligatoria, Electiva).") 
    secciones_disponibles = models.IntegerField(default=1, help_text="Número de secciones en las que se dividirá la materia.") 
    profesores_aptos = models.ManyToManyField(Profesor, related_name='materias_aptas', blank=True, help_text="Profesores calificados para impartir esta materia.")
    carrera_principal = models.CharField(max_length=255, default="Sin Carrera Definida", help_text="Carrera principal a la que pertenece esta materia.") 

    # Campo para requisitos de aula, con validador.
    requisitos_de_aula = models.JSONField(
        null=True, 
        blank=True, 
        default=dict, 
        help_text="Ej: {'tipo_aula': 'Laboratorio', 'recursos_minimos': ['Computadoras', 'Proyector']}",
        validators=[validate_json_schema] # Agregado el validador
    )

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Materias"

class Horario(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='horarios_asignados', help_text="Profesor asignado a este horario.") 
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='horarios_asignados', help_text="Materia asignada a este horario.") 
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='horarios_asignados', help_text="Aula asignada a este horario.") 
    
    DIA_CHOICES = [
        ('LUN', 'Lunes'), ('MAR', 'Martes'), ('MIE', 'Miércoles'), 
        ('JUE', 'Jueves'), ('VIE', 'Viernes'), ('SAB', 'Sábado'), ('DOM', 'Domingo') # Añadí SAB y DOM por si acaso
    ]
    dia = models.CharField(max_length=3, choices=DIA_CHOICES, help_text="Día de la semana del horario.")
    hora_inicio = models.TimeField(help_text="Hora de inicio del bloque horario.")
    hora_fin = models.TimeField(help_text="Hora de fin del bloque horario.")
    tipo_clase = models.CharField(max_length=50, blank=True, null=True, help_text="Tipo de clase (ej. Teoría, Práctica, Laboratorio).") 
    seccion = models.CharField(max_length=10, default="1", help_text="Sección de la materia.") 
    periodo_academico = models.CharField(max_length=20, default="2025-2", help_text="Período académico (ej. 2025-1, 2025-2).") 
    carrera_programa = models.CharField(max_length=100, default="ingeniero en sistemas", help_text="Carrera o programa académico al que pertenece este horario.") 

    class Meta:
        # Asegura que un aula no pueda estar ocupada por dos horarios diferentes en el mismo día y hora.
        # También que un profesor no pueda estar en dos lugares a la vez.
        unique_together = ('aula', 'dia', 'hora_inicio', 'hora_fin', 'periodo_academico') 
        verbose_name_plural = "Horarios"
        ordering = ['dia', 'hora_inicio'] # Para un orden lógico en listas

    def __str__(self):
        return f"{self.materia.nombre} - {self.dia} {self.hora_inicio.strftime('%H:%M')}-{self.hora_fin.strftime('%H:%M')} ({self.profesor.nombre})"

class Restriccion(models.Model):
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo de la restricción.")
    TIPO_CHOICES = [
        ('PROFESOR_NO_DISPONIBLE', 'Profesor No Disponible'),
        ('AULA_NO_DISPONIBLE', 'Aula No Disponible'),
        ('MATERIA_NO_EN_AULA', 'Materia No Puede Usar Aula Específica'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, help_text="Define si la restricción aplica a Profesor, Aula, etc.")
    
    # Días completos en la restricción (para consistencia con Horario)
    DIA_CHOICES = [
        ('LUN', 'Lunes'), ('MAR', 'Martes'), ('MIE', 'Miércoles'), 
        ('JUE', 'Jueves'), ('VIE', 'Viernes'), ('SAB', 'Sábado'), ('DOM', 'Domingo')
    ]
    dia = models.CharField(max_length=3, choices=DIA_CHOICES, null=True, blank=True, help_text="Día de la semana al que aplica la restricción.")
    hora_inicio = models.TimeField(null=True, blank=True, help_text="Hora de inicio del período de restricción.")
    hora_fin = models.TimeField(null=True, blank=True, help_text="Hora de fin del período de restricción.")
    
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True, related_name='restricciones_definidas', help_text="Profesor afectado por esta restricción (si aplica).") 
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, null=True, blank=True, related_name='restricciones_definidas', help_text="Aula afectada por esta restricción (si aplica).") 
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=True, blank=True, related_name='restricciones_definidas', help_text="Materia afectada por esta restricción (si aplica).") 
    
    reglas = models.JSONField(null=True, blank=True, default=dict, help_text="Reglas adicionales en formato JSON (opcional).", validators=[validate_json_schema]) # Asegurado default=dict
    
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción detallada de la restricción.") 

    def __str__(self):
        return f"Restricción de {self.tipo}: {self.nombre}"
    
    class Meta:
        verbose_name_plural = "Restricciones"
        # Se podría considerar unique_together dependiendo de la complejidad y granularidad deseada
        # Por ejemplo, una restricción de "Profesor no disponible" para un día y hora específica.
        # unique_together = ('tipo', 'profesor', 'dia', 'hora_inicio', 'hora_fin') # Ejemplo más estricto

# --------------------------------------------------------------------------------------------------------------------------
# ¡¡¡ NUEVOS MODELOS AÑADIDOS A CONTINUACIÓN !!!
# --------------------------------------------------------------------------------------------------------------------------

# NUEVO MODELO: SolicitudClase
class SolicitudClase(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='solicitudes_clase', help_text="Materia solicitada para la clase.")
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='solicitudes_clase', help_text="Profesor que solicita o impartirá la clase.")
    
    # Campo 'aula' agregado a SolicitudClase para almacenar el aula sugerida del Excel directamente
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='solicitudes_aula', blank=True, null=True, help_text="Aula sugerida para esta solicitud de clase (puede venir del Excel).")
    
    # Campos de día y hora directamente en SolicitudClase si se importan desde Excel
    dia = models.CharField(max_length=3, choices=Horario.DIA_CHOICES, blank=True, null=True, help_text="Día sugerido para la solicitud de clase.")
    hora_inicio = models.TimeField(blank=True, null=True, help_text="Hora de inicio sugerida para la solicitud de clase.")
    hora_fin = models.TimeField(blank=True, null=True, help_text="Hora de fin sugerida para la solicitud de clase.")

    TIPO_CLASE_CHOICES = [
        ('Teoría', 'Teoría'), ('Práctica', 'Práctica'), ('Laboratorio', 'Laboratorio'), ('Seminario', 'Seminario') # Añadí Seminario
    ]
    tipo_clase = models.CharField(max_length=50, choices=TIPO_CLASE_CHOICES, help_text="Tipo de clase solicitada (ej. Teoría, Práctica).")
    seccion = models.CharField(max_length=10, help_text="Sección de la materia solicitada.")
    periodo_academico = models.CharField(max_length=20, help_text="Período académico para el cual se solicita la clase (ej. 2025-1).")
    carrera_programa = models.CharField(max_length=255, help_text="Carrera o programa al que pertenece la solicitud.") # Ajustado a 255 para consistencia

    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Asignada', 'Asignada'),
        ('Cancelada', 'Cancelada'),
        ('Rechazada', 'Rechazada'), # Añadí Rechazada
    ]
    estado = models.CharField(max_length=20, default='Pendiente', choices=ESTADO_CHOICES, help_text="Estado actual de la solicitud (Pendiente, Asignada, Cancelada, Rechazada).")
    
    # Campo para almacenar sugerencias de aula, día, hora si vienen del excel.
    # Este campo ahora es más redundante si `aula`, `dia`, `hora_inicio`, `hora_fin` se mueven directamente a SolicitudClase,
    # pero podría usarse para almacenar "alternativas" o detalles más ricos de la sugerencia original.
    requisitos_aula_sugeridos = models.JSONField(default=dict, blank=True, null=True, validators=[validate_json_schema], help_text="JSON con detalles de los requisitos o sugerencias del aula original del Excel.")

    def __str__(self):
        return f"{self.materia.nombre} - Sec {self.seccion} ({self.tipo_clase}) | Prof: {self.profesor} | Per: {self.periodo_academico} | Estado: {self.estado}"

    class Meta:
        verbose_name_plural = "Solicitudes de Clases"
        # Asegura que no se dupliquen solicitudes idénticas para el mismo período
        unique_together = ('materia', 'profesor', 'tipo_clase', 'seccion', 'periodo_academico', 'carrera_programa')
        ordering = ['periodo_academico', 'materia__nombre', 'seccion'] # Orden lógico

# NUEVO MODELO: VersionHorario
class VersionHorario(models.Model):
    nombre_version = models.CharField(max_length=255, unique=True, help_text="Un nombre descriptivo para esta versión del horario.")
    fecha_guardado = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora en que se guardó esta versión.")
    
    # Campo JSON para almacenar una "instantánea" de todos los horarios activos en ese momento.
    datos_horario_json = models.JSONField(help_text="Copia serializada del conjunto de horarios.", default=list, validators=[validate_json_schema]) # Cambiado a default=list, ya que contendrá una lista de horarios

    def __str__(self):
        return f"{self.nombre_version} - Guardado el {self.fecha_guardado.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name_plural = "Versiones de Horarios"
        ordering = ['-fecha_guardado'] # Ordenar por las más recientes primero