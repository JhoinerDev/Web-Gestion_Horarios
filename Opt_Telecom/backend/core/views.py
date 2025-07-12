from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

# Asegúrate de que tus modelos estén en .models
from .models import Profesor, Materia, Aula, Horario, Restriccion, SolicitudClase, VersionHorario
# Asegúrate de que tus serializadores estén en .serializers
from .serializers import (
    ProfesorSerializer, MateriaSerializer, AulaSerializer, HorarioSerializer, RestriccionSerializer,
    SolicitudClaseSerializer, VersionHorarioSerializer
)

from datetime import datetime, time, timedelta
import json
from django.utils import timezone
import pandas as pd
import numpy as np # Importamos numpy para usar np.nan y pd.isna de forma más robusta
import traceback # Importamos traceback para depuración

# --- Funciones Auxiliares (revisadas y mejoradas) ---

def is_time_in_range(start_time, end_time, current_time):
    """
    Verifica si un tiempo específico (current_time) cae dentro de un rango de tiempo.
    El rango es inclusivo en start_time y exclusivo en end_time.
    Maneja rangos que cruzan la medianoche (ej. 23:00 - 02:00).
    """
    if start_time <= end_time:
        return start_time <= current_time < end_time
    else:  # Rango cruza medianoche (ej. 23:00 - 02:00)
        return start_time <= current_time or current_time < end_time

def excel_time_to_python_time(excel_value):
    """
    Convierte un valor de hora de Excel a un objeto datetime.time de Python.
    Maneja:
    1. Números flotantes/enteros (representación interna de Excel para horas/fechas).
    2. Objetos datetime.time o datetime.datetime (si pandas ya los ha convertido).
    3. Cadenas de texto con varios formatos comunes de hora (HH:MM:SS, HH:MM, con/sin AM/PM).
    """
    if pd.isna(excel_value) or excel_value is None or (isinstance(excel_value, str) and excel_value.strip() == ''):
        return None  # Devuelve None si el valor está vacío o es NaN

    if isinstance(excel_value, (float, int)):
        if 0 <= excel_value < 1:  # Es una fracción de día (hora de Excel)
            total_seconds = excel_value * 24 * 3600
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return time(int(hours), int(minutes), int(seconds))
        else:
            # Podría ser una fecha-hora completa en formato de número de serie de Excel.
            try:
                # El origen '1899-12-30' es el estándar para Excel en Windows para números de serie de fecha/hora.
                dt_obj = pd.to_datetime(excel_value, unit='D', origin='1899-12-30')
                return dt_obj.time()
            except Exception:
                # Si no es una hora ni una fecha válida de Excel, podría ser un número arbitrario
                # que no representa una hora. Se devuelve un error.
                raise ValueError(f"No se pudo convertir el número de serie de Excel a hora o fecha/hora: '{excel_value}'")

    elif isinstance(excel_value, time):
        return excel_value
    elif isinstance(excel_value, datetime):
        return excel_value.time()
    elif isinstance(excel_value, str):
        cleaned_value = excel_value.strip()
        formatos_hora = [
            '%H:%M:%S', '%H:%M',           # 24-horas
            '%I:%M:%S %p', '%I:%M %p',     # 12-horas con AM/PM (ej. "02:30:00 PM")
            '%I:%M:%S %P', '%I:%M %P',     # 12-horas con am/pm (ej. "02:30:00 pm")
            '%H.%M', '%H.%M.%S'            # Para formatos con puntos (ej. "14.30", "14.30.00")
        ]
        for fmt in formatos_hora:
            try:
                # Ajuste: Normalizamos a dos puntos SOLO si el valor de entrada contiene puntos
                parsed_value = cleaned_value.replace('.', ':') if '.' in cleaned_value else cleaned_value
                dt_obj = datetime.strptime(parsed_value, fmt)
                return dt_obj.time()
            except ValueError:
                continue
        raise ValueError(f"Formato de hora de cadena no reconocido: '{cleaned_value}'. Revise el formato del Excel.")
    else:
        raise TypeError(f"Tipo de dato inesperado para la hora: {type(excel_value).__name__} con valor '{excel_value}'")

def clean_col_name(col):
    """
    Función para limpiar y normalizar un nombre de columna para el procesamiento de Excel.
    """
    return str(col).strip().lower().replace(' ', '_').replace('.', '').replace('-', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')

# --- ViewSets existentes ---
class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all().order_by('apellido', 'nombre')
    serializer_class = ProfesorSerializer
    permission_classes = [AllowAny]

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all().order_by('nombre')
    serializer_class = MateriaSerializer
    permission_classes = [AllowAny]

class AulaViewSet(viewsets.ModelViewSet):
    queryset = Aula.objects.all().order_by('codigo')
    serializer_class = AulaSerializer
    permission_classes = [AllowAny]

class RestriccionViewSet(viewsets.ModelViewSet):
    queryset = Restriccion.objects.all().order_by('tipo', 'nombre')
    serializer_class = RestriccionSerializer
    permission_classes = [AllowAny]

class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all().order_by('dia', 'hora_inicio')
    serializer_class = HorarioSerializer
    permission_classes = [AllowAny]

    # La vista `generar_horarios` ahora reside en `GenerarHorariosView` (APIView)
    # y no en HorarioViewSet. Por lo tanto, la eliminamos de aquí.

    @action(detail=False, methods=['delete'])
    def eliminar_horarios(self, request):
        try:
            count, _ = Horario.objects.all().delete()
            return Response({"message": f"Se eliminaron {count} horarios exitosamente."}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = f"Error al eliminar horarios: {str(e)}"
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- NUEVOS VIEWSETS Y APIViews ---

class SolicitudClaseViewSet(viewsets.ModelViewSet):
    queryset = SolicitudClase.objects.all().order_by('periodo_academico', 'materia__nombre', 'seccion')
    serializer_class = SolicitudClaseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        count = SolicitudClase.objects.all().delete()[0]
        return Response({'message': f'Se eliminaron {count} solicitudes de clase.'}, status=status.HTTP_204_NO_CONTENT)


class VersionHorarioViewSet(viewsets.ModelViewSet):
    queryset = VersionHorario.objects.all().order_by('-fecha_guardado')
    serializer_class = VersionHorarioSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        version = get_object_or_404(VersionHorario, pk=pk)
        
        try:
            with transaction.atomic():
                # Eliminar todos los horarios actuales antes de restaurar
                Horario.objects.all().delete()

                restored_count = 0
                errors = []
                
                # Iterar sobre los datos de la versión y crear nuevos objetos Horario
                for horario_data in version.datos_horario_json:
                    try:
                        # Necesitamos obtener las instancias de Profesor, Materia y Aula por sus IDs
                        profesor_id = horario_data.get('profesor')
                        materia_id = horario_data.get('materia')
                        aula_id = horario_data.get('aula')

                        # Asegurarse de que los IDs no sean None antes de buscar
                        if not all([profesor_id, materia_id, aula_id]):
                            raise ValueError("IDs de profesor, materia o aula faltantes en los datos de la versión.")

                        profesor = get_object_or_404(Profesor, pk=profesor_id)
                        materia = get_object_or_404(Materia, pk=materia_id)
                        aula = get_object_or_404(Aula, pk=aula_id)

                        # Conversión segura de horas de string a objetos time
                        hora_inicio = time.fromisoformat(horario_data['hora_inicio'])
                        hora_fin = time.fromisoformat(horario_data['hora_fin'])

                        Horario.objects.create(
                            profesor=profesor,
                            materia=materia,
                            aula=aula,
                            dia=horario_data['dia'],
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            tipo_clase=horario_data.get('tipo_clase'),
                            seccion=horario_data.get('seccion'),
                            periodo_academico=horario_data.get('periodo_academico'),
                            carrera_programa=horario_data.get('carrera_programa')
                        )
                        restored_count += 1
                    except Exception as e:
                        errors.append(f"Error al restaurar horario (ID original {horario_data.get('id', 'N/A')}): {e}. Datos: {horario_data}")
                
                if errors:
                    # Si hay errores, no necesariamente es un rollback total, pero se reportan los errores.
                    # El 200 OK con mensaje de advertencia es adecuado si algunos se restauraron.
                    return Response({
                        "message": f"Se restauraron {restored_count} horarios. Errores al restaurar algunos: {len(errors)}.",
                        "errors": errors
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "message": f"Versión de horario '{version.nombre_version}' restaurada exitosamente. Se crearon {restored_count} horarios."
                    }, status=status.HTTP_200_OK)
        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error general al intentar restaurar la versión: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=True, methods=['get']) # Cambiado a GET para cargar solo datos sin side effects
    def cargar_version(self, request, pk=None):
        """
        Carga una versión de horario guardada y devuelve el JSON.
        Esta vista no modifica la base de datos, solo retorna los datos para ser usados por el frontend.
        """
        version = self.get_object()
        horarios_data_from_json = version.datos_horario_json

        return Response({
            'message': f'Versión "{version.nombre_version}" cargada. Datos de horario devueltos.',
            'horarios_data': horarios_data_from_json
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def guardar_actual(self, request):
        """
        Guarda todos los horarios actualmente activos en la base de datos como una nueva versión.
        Requiere 'nombre_version' en el cuerpo de la solicitud.
        """
        nombre_version = request.data.get('nombre_version')
        if not nombre_version:
            return Response({'error': 'El nombre de la versión es requerido para guardar.'}, status=status.HTTP_400_BAD_REQUEST)

        horarios_actuales = Horario.objects.all().order_by('dia', 'hora_inicio')
        datos_para_json = HorarioSerializer(horarios_actuales, many=True).data

        try:
            version = VersionHorario.objects.create(
                nombre_version=nombre_version,
                datos_horario_json=datos_para_json
            )
            serializer = VersionHorarioSerializer(version)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'No se pudo guardar la versión del horario: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- VISTA PARA IMPORTAR SOLICITUDES DE CLASE DESDE EXCEL ---
class ImportarHorariosExcelView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'error': 'No se proporcionó ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if not file.name.lower().endswith(('.xls', '.xlsx')):
            return Response({'error': 'Formato de archivo no soportado. Por favor, sube un archivo Excel (.xls o .xlsx).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)

            # Normalización más robusta de nombres de columnas
            df.columns = [clean_col_name(col) for col in df.columns]

            # Mapeo de nombres de columnas normalizados a los nombres esperados en nuestro código
            # Agregamos 'carrera_programa_excel' como posible alias si la carrera viene del mismo campo que el periodo.
            column_aliases = {
                'dia': ['dia', 'day'],
                'hora_inicio': ['hora_inicio', 'hora_ini', 'start_time'],
                'hora_fin': ['hora_fin', 'hora_final', 'end_time'],
                'profesor': ['profesor', 'nombre_profesor', 'profesor_nombre'],
                'materia': ['materia', 'nombre_materia'],
                'aula': ['aula', 'codigo_aula', 'nombre_aula'],
                'tipo_clase': ['tipo_clase', 'clase_tipo', 'class_type'],
                'seccion': ['seccion', 'section', 'seccion_num'],
                'periodo_academico_carrera': ['periodo_academico_carrera', 'periodo_academico', 'periodo_carrera'] # Campo combinado de Excel
            }

            # Definir las columnas que realmente esperamos para crear la SolicitudClase.
            # NO esperamos un campo combinado 'periodo_academico_carrera_programa' en el DataFrame final,
            # sino que procesaremos 'periodo_academico_carrera' del Excel para obtener 'periodo_academico' y 'carrera_programa'.
            required_excel_columns_for_processing = [
                'dia', 'hora_inicio', 'hora_fin',
                'profesor', 'materia', 'aula',
                'tipo_clase', 'seccion', 'periodo_academico_carrera' # Aquí esperamos el campo combinado del Excel
            ]
            
            # Verificar si todas las columnas requeridas existen en el DataFrame después de la normalización
            for expected_col_key, possible_names in column_aliases.items():
                found = False
                for pn in possible_names:
                    if pn in df.columns:
                        found = True
                        break
                if not found and expected_col_key in [col for col_list in column_aliases.values() for col in col_list]: # Solo si es una columna esperada en el input
                    if expected_col_key in required_excel_columns_for_processing: # Y si es una de las que sí o sí necesitamos
                        return Response({
                            'error': f'Columna requerida faltante o con nombre incorrecto en el archivo Excel: "{expected_col_key}" (posibles nombres: {", ".join(possible_names)}). Por favor, revise su archivo.'
                        }, status=status.HTTP_400_BAD_REQUEST)

            created_solicitudes = []
            errors = []
            imported_count = 0

            # Diccionario para mapear días de la semana (ej. 'Lunes' a 'LUN')
            dias_map = {
                'lunes': 'LUN', 'lun': 'LUN',
                'martes': 'MAR', 'mar': 'MAR',
                'miércoles': 'MIE', 'miercoles': 'MIE', 'mie': 'MIE',
                'jueves': 'JUE', 'jue': 'JUE',
                'viernes': 'VIE', 'vie': 'VIE',
                'sábado': 'SAB', 'sabado': 'SAB', 'sab': 'SAB',
                'domingo': 'DOM', 'dom': 'DOM',
            }

            for index, row in df.iterrows():
                try:
                    with transaction.atomic():
                        # Obtener valores de la fila de forma segura, usando aliases si es necesario
                        # Y manejar valores NaN/None con cadenas vacías
                        def get_row_value(row, aliases):
                            for alias in aliases:
                                if alias in row and pd.notna(row[alias]):
                                    return str(row[alias]).strip()
                            return ""

                        profesor_full_name = get_row_value(row, column_aliases['profesor'])
                        materia_nombre = get_row_value(row, column_aliases['materia'])
                        aula_codigo = get_row_value(row, column_aliases['aula'])
                        tipo_clase = get_row_value(row, column_aliases['tipo_clase'])
                        seccion_str = get_row_value(row, column_aliases['seccion'])
                        periodo_carrera_excel = get_row_value(row, column_aliases['periodo_academico_carrera'])
                        dia_excel = get_row_value(row, column_aliases['dia'])

                        hora_inicio_excel = row[next((alias for alias in column_aliases['hora_inicio'] if alias in row), None)]
                        hora_fin_excel = row[next((alias for alias in column_aliases['hora_fin'] if alias in row), None)]

                        # Validaciones de datos básicos
                        if not all([profesor_full_name, materia_nombre, aula_codigo, tipo_clase, seccion_str, periodo_carrera_excel, dia_excel]):
                            raise ValueError("Una o más columnas críticas están vacías.")

                        # 1. Procesar Profesor: Obtener o crear
                        profesor_parts = profesor_full_name.split(' ', 1)
                        nombre_profesor = profesor_parts[0] if profesor_parts else ""
                        apellido_profesor = profesor_parts[1] if len(profesor_parts) > 1 else ""

                        if not nombre_profesor: # Si el nombre está vacío, no se puede buscar/crear
                            raise ValueError("El nombre del profesor está vacío.")

                        profesor, created_prof = Profesor.objects.get_or_create(
                            nombre=nombre_profesor,
                            apellido=apellido_profesor,
                            defaults={
                                'especialidad': 'General',
                                'carga_horaria_maxima': 40
                            }
                        )

                        # 2. Procesar Materia: Obtener o crear
                        if not materia_nombre:
                            raise ValueError("El nombre de la materia está vacío.")
                            
                        materia, created_mat = Materia.objects.get_or_create(
                            nombre=materia_nombre,
                            defaults={
                                'horas_semanales': 0,
                                'horas_teoricas': 0,
                                'horarios_de_practicas': 0,
                                'horario_de_laboratorio': 0,
                                'secciones_disponibles': 1,
                            }
                        )
                        # NOTA: Si el modelo Materia tuviera 'carrera_principal', deberías añadirlo aquí en defaults.
                        # Asumiendo que no lo tiene basándonos en tu FieldError anterior.

                        # 3. Procesar Aula: Obtener o crear
                        if not aula_codigo:
                            raise ValueError("El código del aula está vacío.")

                        aula, created_aula = Aula.objects.get_or_create(
                            codigo=aula_codigo,
                            defaults={
                                'capacidad': 0,
                                'tipo': 'General',
                            }
                        )

                        # 4. Procesar Día y Horas
                        dia_normalizado = dias_map.get(dia_excel.lower(), None)
                        if dia_normalizado is None:
                            raise ValueError(f"Día de la semana no reconocido: '{dia_excel}'.")

                        hora_inicio = excel_time_to_python_time(hora_inicio_excel)
                        hora_fin = excel_time_to_python_time(hora_fin_excel)

                        if hora_inicio is None or hora_fin is None:
                            raise ValueError("Las horas de inicio o fin no son válidas.")
                        if hora_inicio >= hora_fin and not (hora_inicio > hora_fin and hora_fin < time(6,0)): # Permite cruzar medianoche de 23:00 a 02:00, pero no inválidos.
                             raise ValueError("La hora de inicio debe ser anterior a la hora de fin, o el rango debe cruzar la medianoche de forma válida.")

                        # 5. Procesar Periodo Académico y Carrera/Programa
                        periodo_academico = "N/A"
                        carrera_programa = "N/A"
                        
                        # Intenta parsear el formato "YYYY-P Carrera Nombre" o "YYYY-P"
                        if ' ' in periodo_carrera_excel:
                            parts_periodo_carrera = periodo_carrera_excel.split(' ', 1)
                            periodo_academico = parts_periodo_carrera[0].strip()
                            carrera_programa = parts_periodo_carrera[1].strip()
                        else:
                            periodo_academico = periodo_carrera_excel.strip()
                            # Si no hay carrera en el string, la asumimos de la materia si aplica,
                            # o un valor por defecto si no.
                            # Para el caso de la solicitud, 'carrera_programa' proviene del Excel o de un default.
                            carrera_programa = "No Especificada en Excel"

                        # Construir el JSON para requisitos_aula_sugeridos (opcional, si el frontend lo usa)
                        requisitos_aula_sugeridos_json = {
                            'aula_codigo_sugerida': aula_codigo,
                            'dia_sugerido': dia_normalizado,
                            'hora_inicio_sugerida': hora_inicio.isoformat(),
                            'hora_fin_sugerida': hora_fin.isoformat(),
                        }

                        # 6. Crear SolicitudClase
                        solicitud = SolicitudClase.objects.create(
                            materia=materia,
                            profesor=profesor,
                            aula=aula, # El aula sugerida directamente del Excel
                            dia=dia_normalizado,
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            tipo_clase=tipo_clase,
                            seccion=seccion_str,
                            periodo_academico=periodo_academico,
                            carrera_programa=carrera_programa,
                            requisitos_aula_sugeridos=requisitos_aula_sugeridos_json,
                            estado='Pendiente'
                        )
                        created_solicitudes.append(solicitud)
                        imported_count += 1

                except Exception as e:
                    errors.append({
                        'fila': index + 2,
                        'error': str(e),
                        'data': row.to_dict()
                    })

            if errors:
                return Response({
                    'message': f'Se procesaron {imported_count} solicitudes. Se encontraron {len(errors)} errores. Revise los detalles.',
                    'solicitudes_creadas': SolicitudClaseSerializer(created_solicitudes, many=True).data,
                    'errors': errors
                }, status=status.HTTP_207_MULTI_STATUS)
            else:
                return Response({
                    'message': f'Se importaron {imported_count} solicitudes exitosamente.',
                    'solicitudes_creadas': SolicitudClaseSerializer(created_solicitudes, many=True).data
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error inesperado al procesar el archivo Excel: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- VISTA PARA ASIGNAR SOLICITUD A HORARIO ---
class AsignarSolicitudAHorarioView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk=None):
        try:
            solicitud = get_object_or_404(SolicitudClase, pk=pk)

            horario_data = request.data

            required_horario_fields = ['aula', 'dia', 'hora_inicio', 'hora_fin']
            if not all(field in horario_data for field in required_horario_fields):
                return Response(
                    {'error': f'Faltan campos requeridos para crear el horario: {", ".join(required_horario_fields)}. Asegúrate de enviar: aula (ID), dia, hora_inicio, hora_fin.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Convertir horas de string a objetos time
            try:
                if isinstance(horario_data.get('hora_inicio'), str):
                    horario_data['hora_inicio'] = time.fromisoformat(horario_data['hora_inicio'])
                if isinstance(horario_data.get('hora_fin'), str):
                    horario_data['hora_fin'] = time.fromisoformat(horario_data['hora_fin'])
            except ValueError as ve:
                return Response({'error': f'Formato de hora inválido en horario_data: {str(ve)}'}, status=status.HTTP_400_BAD_REQUEST)

            # Rellenar datos del horario con la información de la solicitud
            horario_data['profesor'] = solicitud.profesor.id
            horario_data['materia'] = solicitud.materia.id
            horario_data['aula'] = int(horario_data['aula']) # Asegura que sea un entero para el FK
            horario_data['tipo_clase'] = solicitud.tipo_clase
            horario_data['seccion'] = solicitud.seccion
            horario_data['periodo_academico'] = solicitud.periodo_academico
            horario_data['carrera_programa'] = solicitud.carrera_programa

            # Crear el serializador de Horario y validar
            horario_serializer = HorarioSerializer(data=horario_data)

            if horario_serializer.is_valid():
                with transaction.atomic():
                    # Antes de guardar, verificar conflictos de horario para el aula, profesor, y sección
                    # Conflicto de aula: ¿Está el aula ocupada en ese día y franja horaria?
                    if Horario.objects.filter(
                        aula_id=horario_data['aula'],
                        dia=horario_data['dia'],
                        hora_inicio=horario_data['hora_inicio'],
                        hora_fin=horario_data['hora_fin'],
                        periodo_academico=horario_data['periodo_academico']
                    ).exists():
                        return Response({'error': 'El aula ya está ocupada en ese horario para este período.'}, status=status.HTTP_409_CONFLICT) # 409 Conflict

                    # Conflicto de profesor: ¿Está el profesor ocupado en ese día y franja horaria?
                    if Horario.objects.filter(
                        profesor_id=horario_data['profesor'],
                        dia=horario_data['dia'],
                        hora_inicio=horario_data['hora_inicio'],
                        hora_fin=horario_data['hora_fin'],
                        periodo_academico=horario_data['periodo_academico']
                    ).exists():
                        return Response({'error': 'El profesor ya está ocupado en ese horario para este período.'}, status=status.HTTP_409_CONFLICT)

                    # Conflicto de sección: ¿Ya hay una clase asignada para la misma materia y sección en ese slot?
                    # Esto evita duplicados para la misma sección
                    if Horario.objects.filter(
                        materia_id=horario_data['materia'],
                        seccion=horario_data['seccion'],
                        dia=horario_data['dia'],
                        hora_inicio=horario_data['hora_inicio'],
                        hora_fin=horario_data['hora_fin'],
                        periodo_academico=horario_data['periodo_academico']
                    ).exists():
                        return Response({'error': 'Ya existe un horario para esta materia y sección en el slot seleccionado.'}, status=status.HTTP_409_CONFLICT)


                    horario = horario_serializer.save()
                    solicitud.estado = 'Asignada'
                    solicitud.save()

                return Response({
                    'message': 'Solicitud asignada y horario creado exitosamente.',
                    'solicitud': SolicitudClaseSerializer(solicitud).data,
                    'horario': HorarioSerializer(horario).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(horario_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SolicitudClase.DoesNotExist:
            return Response({'error': 'Solicitud de clase no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response({'error': f'Error en el formato de datos proporcionados: {str(ve)}. Asegúrate de que los IDs sean números enteros y las horas válidas.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error al asignar solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- VISTA PARA DISPARAR ALGORITMO DE GENERACIÓN (AHORA ES UNA APIView) ---
class GenerarHorariosView(APIView):
    permission_classes = [AllowAny] # Permite que cualquier usuario la use (ajusta si requieres autenticación)

    def post(self, request, *args, **kwargs):
        # Esta vista fue trasladada y adaptada desde HorarioViewSet.generar_horarios
        count_deleted = 0
        try:
            with transaction.atomic(): # Asegura que toda la generación sea atómica

                # 1. Limpiar horarios existentes para empezar desde un estado limpio en cada generación
                count_deleted, _ = Horario.objects.all().delete()
                print(f"Se eliminaron {count_deleted} horarios existentes antes de generar nuevos.")

                # 2. Obtener todos los datos maestros necesarios
                profesores = Profesor.objects.all()
                materias = Materia.objects.all()
                aulas = Aula.objects.all()
                restricciones = Restriccion.objects.all()
                solicitudes_pendientes = SolicitudClase.objects.filter(estado='Pendiente').order_by('materia__nombre', 'seccion', 'dia', 'hora_inicio')


                # 3. Validar que existan datos básicos para la generación
                if not profesores.exists():
                    return Response({"message": "No hay profesores registrados. Crea al menos uno en el admin."}, status=status.HTTP_400_BAD_REQUEST)
                if not materias.exists():
                    return Response({"message": "No hay materias registradas. Crea al menos una en el admin."}, status=status.HTTP_400_BAD_REQUEST)
                if not aulas.exists():
                    return Response({"message": "No hay aulas registradas. Crea al menos una en el admin."}, status=status.HTTP_400_BAD_REQUEST)
                # Si no hay solicitudes, el algoritmo no tiene qué asignar, pero podría generar basándose en reglas generales
                # if not solicitudes_pendientes.exists():
                #     return Response({"message": "No hay solicitudes de clase pendientes para generar horarios. Por favor, importe solicitudes."}, status=status.HTTP_400_BAD_REQUEST)


                # 4. Estructuras de datos para el algoritmo
                horarios_generados = [] # Para almacenar los horarios creados en esta ejecución

                # Diccionarios para llevar el control de carga por profesor y ocupación de aulas/profesores
                carga_horaria_profesor_actual = {p.id: 0 for p in profesores}
                # Seguimiento de ocupación de slots: {(dia, hora_inicio, aula_id): True}
                ocupacion_aulas = {}
                # Seguimiento de ocupación de slots: {(dia, hora_inicio, profesor_id): True}
                ocupacion_profesores = {}
                # Seguimiento de ocupación de slots: {(dia, hora_inicio, materia_id, seccion): True}
                ocupacion_secciones = {}


                # Días de la semana y franjas horarias base para la iteración
                dias_semana = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']
                # Considera que estas franjas deben ser un conjunto flexible de slots.
                # Se pueden definir más granularmente (ej. cada hora) y luego el algoritmo busca el espacio necesario.
                franjas_horarias_standard = [
                    (time(8, 0), time(10, 0)),
                    (time(10, 0), time(12, 0)),
                    (time(14, 0), time(16, 0)),
                    (time(16, 0), time(18, 0)),
                ]

                # 5. Pre-procesar restricciones para una consulta eficiente
                # Optimizamos la estructura de restricciones
                restricciones_map = {
                    dia: {'aulas': {}, 'profesores': {}, 'materias_no_en_aula': {}}
                    for dia in dias_semana
                }
                for res in restricciones:
                    try:
                        res_dia = res.dia
                        if res_dia not in restricciones_map:
                             print(f"ADVERTENCIA: Restricción '{res.nombre}' con día '{res_dia}' no reconocido. Saltando.")
                             continue

                        if res.tipo == 'AULA_NO_DISPONIBLE' and res.aula and res.hora_inicio and res.hora_fin:
                            aula_id = res.aula.id
                            if aula_id not in restricciones_map[res_dia]['aulas']:
                                restricciones_map[res_dia]['aulas'][aula_id] = []
                            restricciones_map[res_dia]['aulas'][aula_id].append((res.hora_inicio, res.hora_fin))
                        elif res.tipo == 'PROFESOR_NO_DISPONIBLE' and res.profesor and res.hora_inicio and res.hora_fin:
                            profesor_id = res.profesor.id
                            if profesor_id not in restricciones_map[res_dia]['profesores']:
                                restricciones_map[res_dia]['profesores'][profesor_id] = []
                            restricciones_map[res_dia]['profesores'][profesor_id].append((res.hora_inicio, res.hora_fin))
                        elif res.tipo == 'MATERIA_NO_EN_AULA' and res.materia and res.aula:
                            # Esta restricción requiere una lógica diferente.
                            # Se mapea como: {materia_id: [aula_id, aula_id_2]} para las aulas prohibidas para esa materia.
                            if res.materia.id not in restricciones_map[res_dia]['materias_no_en_aula']:
                                restricciones_map[res_dia]['materias_no_en_aula'][res.materia.id] = set()
                            restricciones_map[res_dia]['materias_no_en_aula'][res.materia.id].add(res.aula.id)
                        else:
                            print(f"ADVERTENCIA: Restricción '{res.nombre}' incompleta o tipo no soportado. Saltando.")
                    except Exception as e:
                        print(f"ERROR procesando restricción '{getattr(res, 'nombre', 'N/A')}': {e}. Trace: {traceback.format_exc()}")

                # --- ALGORITMO PRINCIPAL DE GENERACIÓN ---
                # Priorizar solicitudes pendientes
                for solicitud in solicitudes_pendientes:
                    print(f"\n--- Intentando asignar slot para Solicitud: {solicitud.materia.nombre} (Secc {solicitud.seccion}, {solicitud.tipo_clase}) ---")

                    # Validar datos de la solicitud
                    if not all([solicitud.profesor, solicitud.materia, solicitud.aula, solicitud.dia, solicitud.hora_inicio, solicitud.hora_fin, solicitud.tipo_clase, solicitud.seccion, solicitud.periodo_academico, solicitud.carrera_programa]):
                        print(f"  ADVERTENCIA: Solicitud {solicitud.id} tiene datos incompletos. Saltando.")
                        continue

                    # Usar los datos sugeridos por la solicitud como primera opción
                    dia_sugerido = solicitud.dia
                    hora_inicio_sugerida = solicitud.hora_inicio
                    hora_fin_sugerida = solicitud.hora_fin
                    aula_sugerida = solicitud.aula # Objeto Aula

                    profesor_seleccionado = solicitud.profesor # El profesor de la solicitud
                    materia_seleccionada = solicitud.materia
                    
                    # Validar si el slot sugerido por la solicitud es viable
                    slot_viable = True

                    # 1. Carga horaria del profesor
                    duracion_slot_solicitud = (datetime.combine(datetime.min, hora_fin_sugerida) - datetime.combine(datetime.min, hora_inicio_sugerida)).total_seconds() / 3600
                    if profesor_seleccionado.carga_horaria_maxima is not None and \
                       (carga_horaria_profesor_actual[profesor_seleccionado.id] + duracion_slot_solicitud) > profesor_seleccionado.carga_horaria_maxima:
                        print(f"  > Profesor '{profesor_seleccionado.nombre}' excede carga horaria máxima con este slot. Carga actual: {carga_horaria_profesor_actual[profesor_seleccionado.id]}h, Máx: {profesor_seleccionado.carga_horaria_maxima}h. Saltando slot sugerido.")
                        slot_viable = False
                    
                    if not slot_viable: continue

                    # 2. Disponibilidad del profesor (JSONField)
                    profesor_disponibilidad = profesor_seleccionado.disponibilidad
                    if not isinstance(profesor_disponibilidad, dict):
                        print(f"  > ERROR: Disponibilidad de profesor {profesor_seleccionado.nombre} NO es un diccionario válido. Asumiendo no disponible. VERIFICA EL ADMIN.")
                        profesor_disponibilidad = {}

                    if dia_sugerido not in profesor_disponibilidad:
                        print(f"  > Profesor '{profesor_seleccionado.nombre}' no tiene disponibilidad definida para {dia_sugerido}. Saltando slot sugerido.")
                        slot_viable = False
                    else:
                        disponible_en_franja = False
                        for rango_str in profesor_disponibilidad.get(dia_sugerido, []):
                            try:
                                if not isinstance(rango_str, str) or '-' not in rango_str:
                                    print(f"    ADVERTENCIA: Formato de rango horario inválido '{rango_str}' para profesor {profesor_seleccionado.nombre} el {dia_sugerido}. Esperado 'HH:MM-HH:MM'.")
                                    continue
                                disp_start_str, disp_end_str = rango_str.split('-')
                                disp_start_time = time.fromisoformat(disp_start_str)
                                disp_end_time = time.fromisoformat(disp_end_str)

                                # Verificar si el slot sugerido está COMPLETAMENTE dentro de un rango de disponibilidad del profesor
                                if (is_time_in_range(disp_start_time, disp_end_time, hora_inicio_sugerida) and
                                    is_time_in_range(disp_start_time, disp_end_time, (datetime.combine(datetime.min, hora_fin_sugerida) - timedelta(minutes=1)).time())):
                                    disponible_en_franja = True
                                    break
                            except ValueError as ve:
                                print(f"    ADVERTENCIA: Error en formato de hora '{rango_str}' para profesor {profesor_seleccionado.nombre} el {dia_sugerido}: {ve}. Saltando este rango.")
                                continue
                        if not disponible_en_franja:
                            print(f"  > Profesor '{profesor_seleccionado.nombre}' no está disponible en la franja {hora_inicio_sugerida}-{hora_fin_sugerida} el {dia_sugerido}. Saltando slot sugerido.")
                            slot_viable = False

                    if not slot_viable: continue

                    # 3. Restricciones de Profesor (del modelo Restriccion)
                    prof_restricciones_dia = restricciones_map[dia_sugerido]['profesores'].get(profesor_seleccionado.id, [])
                    es_restringido_profesor = False
                    for res_start, res_end in prof_restricciones_dia:
                        if (is_time_in_range(res_start, res_end, hora_inicio_sugerida) and
                            is_time_in_range(res_start, res_end, (datetime.combine(datetime.min, hora_fin_sugerida) - timedelta(minutes=1)).time())):
                            es_restringido_profesor = True
                            break
                    if es_restringido_profesor:
                        print(f"  > Profesor '{profesor_seleccionado.nombre}' está restringido en la franja sugerida. Saltando slot sugerido.")
                        slot_viable = False
                    
                    if not slot_viable: continue

                    # 4. Ocupación de Profesor (ya hay un horario asignado en ese slot)
                    if (dia_sugerido, hora_inicio_sugerida, profesor_seleccionado.id) in ocupacion_profesores:
                         print(f"  > Profesor '{profesor_seleccionado.nombre}' ya ocupado en el slot sugerido. Saltando slot sugerido.")
                         slot_viable = False

                    if not slot_viable: continue

                    # 5. Restricciones de Aula (del modelo Restriccion)
                    aula_restricciones_dia = restricciones_map[dia_sugerido]['aulas'].get(aula_sugerida.id, [])
                    es_restringido_aula = False
                    for res_start, res_end in aula_restricciones_dia:
                        if (is_time_in_range(res_start, res_end, hora_inicio_sugerida) and
                            is_time_in_range(res_start, res_end, (datetime.combine(datetime.min, hora_fin_sugerida) - timedelta(minutes=1)).time())):
                            es_restringido_aula = True
                            break
                    if es_restringido_aula:
                        print(f"  > Aula '{aula_sugerida.codigo}' está restringida en la franja sugerida. Saltando slot sugerido.")
                        slot_viable = False
                    
                    if not slot_viable: continue

                    # 6. Ocupación de Aula (ya hay un horario asignado en ese slot)
                    if (dia_sugerido, hora_inicio_sugerida, aula_sugerida.id) in ocupacion_aulas:
                        print(f"  > Aula '{aula_sugerida.codigo}' ya ocupada en el slot sugerido. Saltando slot sugerido.")
                        slot_viable = False

                    if not slot_viable: continue

                    # 7. Ocupación de Sección (evitar que la misma sección tenga dos clases al mismo tiempo)
                    if (dia_sugerido, hora_inicio_sugerida, materia_seleccionada.id, solicitud.seccion) in ocupacion_secciones:
                        print(f"  > La sección '{solicitud.seccion}' de '{materia_seleccionada.nombre}' ya tiene una clase en el slot sugerido. Saltando slot sugerido.")
                        slot_viable = False

                    if not slot_viable: continue

                    # 8. Requisitos de Aula para la Materia (JSONField materia.requisitos_de_aula)
                    cumple_requisitos_aula = True
                    materia_requisitos_aula = materia_seleccionada.requisitos_de_aula
                    if not isinstance(materia_requisitos_aula, dict):
                        materia_requisitos_aula = {} # Asegura que sea un diccionario

                    if materia_requisitos_aula.get('tipo_aula') and aula_sugerida.tipo != materia_requisitos_aula['tipo_aula']:
                        print(f"  > Aula '{aula_sugerida.codigo}' tipo '{aula_sugerida.tipo}' no cumple con tipo requerido '{materia_requisitos_aula['tipo_aula']}' para materia '{materia_seleccionada.nombre}'.")
                        cumple_requisitos_aula = False

                    aula_recursos = aula_sugerida.recursos_especiales if isinstance(aula_sugerida.recursos_especiales, list) else []
                    if cumple_requisitos_aula and 'recursos_minimos' in materia_requisitos_aula and isinstance(materia_requisitos_aula['recursos_minimos'], list):
                        for recurso_min in materia_requisitos_aula['recursos_minimos']:
                            if recurso_min not in aula_recursos:
                                print(f"  > Aula '{aula_sugerida.codigo}' no tiene el recurso mínimo '{recurso_min}' requerido por la materia '{materia_seleccionada.nombre}'.")
                                cumple_requisitos_aula = False
                                break
                    
                    if not cumple_requisitos_aula:
                        print(f"  > El aula sugerida '{aula_sugerida.codigo}' no cumple los requisitos de la materia. Saltando slot sugerido.")
                        slot_viable = False
                    
                    if not slot_viable: continue

                    # Si llegamos aquí, el slot sugerido es viable
                    if slot_viable:
                        try:
                            # Creamos el nuevo horario
                            nuevo_horario = Horario.objects.create(
                                dia=dia_sugerido,
                                hora_inicio=hora_inicio_sugerida,
                                hora_fin=hora_fin_sugerida,
                                profesor=profesor_seleccionado,
                                materia=materia_seleccionada,
                                aula=aula_sugerida,
                                tipo_clase=solicitud.tipo_clase,
                                seccion=solicitud.seccion,
                                periodo_academico=solicitud.periodo_academico,
                                carrera_programa=solicitud.carrera_programa
                            )
                            horarios_generados.append(HorarioSerializer(nuevo_horario).data)

                            # Actualizar el estado de la solicitud
                            solicitud.estado = 'Asignada'
                            solicitud.save()

                            # Actualizar el control de ocupación
                            carga_horaria_profesor_actual[profesor_seleccionado.id] += duracion_slot_solicitud
                            ocupacion_aulas[(dia_sugerido, hora_inicio_sugerida, aula_sugerida.id)] = True
                            ocupacion_profesores[(dia_sugerido, hora_inicio_sugerida, profesor_seleccionado.id)] = True
                            ocupacion_secciones[(dia_sugerido, hora_inicio_sugerida, materia_seleccionada.id, solicitud.seccion)] = True


                            print(f"  Horario ASIGNADO desde Solicitud: {solicitud.materia.nombre} (Secc {solicitud.seccion}, {solicitud.tipo_clase}) con {profesor_seleccionado.nombre} en {aula_sugerida.codigo} el {dia_sugerido} de {hora_inicio_sugerida.strftime('%H:%M')} a {hora_fin_sugerida.strftime('%H:%M')}.")
                            
                        except Exception as e:
                            print(f"  ERROR INESPERADO al crear horario para Solicitud {solicitud.id}: {e}. Trace: {traceback.format_exc()}")
                            # Marcar la solicitud como 'Error' o 'No Asignada' si falla la creación del horario
                            solicitud.estado = 'Error' # O 'No Asignada' si tienes ese estado
                            solicitud.save()
                            # El transaction.atomic() superior manejará el rollback si hay un error crítico
                            # Aquí solo registramos el error específico de esta solicitud.
                    else:
                        print(f"  ADVERTENCIA: Solicitud {solicitud.id} ({solicitud.materia.nombre} Secc {solicitud.seccion}) NO pudo ser asignada con el slot sugerido. Intentando buscar slot alternativo...")
                        # Si el slot sugerido falla, intentar buscar uno alternativo.
                        # Este es el bloque donde se implementaría la lógica de búsqueda de alternativas
                        # si la solicitud no puede ser asignada en su slot ideal.
                        # Por ahora, si no se asigna en el ideal, se salta.
                        # La complejidad aquí es alta: buscar el mismo profesor/materia en otro slot/aula.
                        print(f"    (Lógica para encontrar slot alternativo no implementada, saltando solicitud {solicitud.id})")
                        solicitud.estado = 'Pendiente' # Mantiene el estado si no se pudo asignar
                        solicitud.save()

                # --- Lógica para asignar horas restantes de materias sin solicitudes o con solicitudes no asignadas ---
                # Esta parte del algoritmo intentaría llenar los huecos o materias sin solicitudes.
                # Puedes decidir si ejecutar esto SIEMPRE o solo si NO hay solicitudes.
                print("\n--- Intentando asignar horas a materias que aún necesitan slots (considerando las no cubiertas por solicitudes) ---")

                # Recalcular las horas restantes por materia para las que NO tienen solicitudes asignadas o completas
                # O para materias que necesitan más horas de las cubiertas por solicitudes.
                # Aquí, podrías iterar por `materia` y luego por `secciones` de esa materia
                # para asignar las horas necesarias, similar a la lógica original que tenías.
                
                # Por simplicidad en la corrección, no re-implementaré la lógica de asignación
                # basada puramente en Materia.horas_semanales si ya tienes SolicitudesClase.
                # Si el flujo principal es a través de SolicitudesClase, entonces la mayoría de los
                # horarios deberían venir de ahí. Si necesitas un algoritmo que genere
                # independientemente de las solicitudes, sería un flujo diferente o complementario.
                # De momento, la generación se enfoca en las solicitudes pendientes.

                # Si no se generaron horarios a partir de solicitudes, pero existen solicitudes,
                # esto indicaría un problema o falta de viabilidad.
                if not horarios_generados and solicitudes_pendientes.exists():
                     return Response({
                        "message": "Algoritmo finalizado. No se pudieron generar horarios para las solicitudes pendientes. Revisa la disponibilidad de profesores, aulas, restricciones y la validez de las solicitudes.",
                        "detalles_horarios": horarios_generados,
                        "carga_profesores_final": carga_horaria_profesor_actual,
                    }, status=status.HTTP_200_OK) # O 400 BAD REQUEST si es un error de configuración
                
                # Al final de la generación exitosa, se puede guardar una "versión"
                try:
                    # Genera un nombre de versión por defecto. Puedes permitir que el usuario lo provea en la request.
                    nombre_version_auto = f"Algoritmo {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                    current_horarios = Horario.objects.all() # Obtener todos los horarios creados por el algoritmo
                    version_data = {
                        'nombre_version': nombre_version_auto,
                        'datos_horario_json': HorarioSerializer(current_horarios, many=True).data
                    }
                    version_serializer = VersionHorarioSerializer(data=version_data)
                    if version_serializer.is_valid(raise_exception=True):
                        version_serializer.save()
                        print(f"Versión de horario '{nombre_version_auto}' guardada exitosamente.")
                except Exception as e:
                    print(f"ERROR al guardar la versión automática del horario: {e}. Trace: {traceback.format_exc()}")
                    # No es un error fatal para la generación del horario, solo para el guardado de la versión.

            # Respuesta final si la transacción atómica fue exitosa
            return Response({
                "message": "Generación de horarios finalizada.",
                "horarios_generados_count": len(horarios_generados),
                "detalles_horarios": horarios_generados,
                "carga_profesores_final": carga_horaria_profesor_actual,
                # Puedes agregar más detalles si lo deseas, ej. solicitudes no asignadas
                "solicitudes_pendientes_tras_algoritmo": SolicitudClaseSerializer(
                    SolicitudClase.objects.filter(estado='Pendiente'), many=True
                ).data
            }, status=status.HTTP_200_OK)


        except Exception as e:
            # Captura cualquier excepción no manejada y asegura un rollback si la transacción está activa.
            # transaction.atomic() ya maneja el rollback si hay una excepción dentro de su bloque.
            traceback.print_exc()  # Imprime el stack trace completo para depuración
            print(f"ERROR GENERAL EN LA GENERACIÓN DE HORARIOS. Horarios eliminados antes del error: {count_deleted}. Error: {str(e)}")
            return Response({"error": f"Error en la generación de horarios: {str(e)}. Por favor, revise la consola del servidor para más detalles."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)