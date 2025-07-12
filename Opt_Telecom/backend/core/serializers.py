# backend/core/serializers.py
import datetime
from datetime import time, timedelta, datetime # Importa datetime (la clase), time y timedelta
from rest_framework import serializers
# Asegúrate de importar los nuevos modelos: SolicitudClase y VersionHorario
from .models import Profesor, Materia, Aula, Horario, Restriccion, SolicitudClase, VersionHorario
import json # Importamos json, aunque no se usa directamente en este serializador, es buena práctica si manejamos JSONFields.

# --- Serializadores existentes (MODIFICADOS) ---

class ProfesorSerializer(serializers.ModelSerializer):
    carga_horaria_asignada = serializers.SerializerMethodField()

    class Meta:
        model = Profesor
        fields = '__all__'

    def get_carga_horaria_asignada(self, obj):
        total_minutes = 0
        for horario in obj.horarios_asignados.all():
            start_dt = horario.hora_inicio
            end_dt = horario.hora_fin
            
            # --- CORRECCIÓN CLAVE AQUÍ ---
            # Usamos 'datetime.combine' ya que 'datetime' (la clase) fue importada directamente
            # y 'datetime.min.date()' para obtener la fecha mínima
            if end_dt < start_dt:
                duration_td = (datetime.combine(datetime.min.date(), time(23, 59, 59)) - datetime.combine(datetime.min.date(), start_dt)) + \
                              (datetime.combine(datetime.min.date(), end_dt) - datetime.combine(datetime.min.date(), time(0, 0, 0))) + \
                              timedelta(seconds=1)
            else:
                duration_td = datetime.combine(datetime.min.date(), end_dt) - datetime.combine(datetime.min.date(), start_dt)
            
            total_minutes += duration_td.total_seconds() / 60
        
        return total_minutes / 60


class MateriaSerializer(serializers.ModelSerializer):
    profesores_aptos_nombres = serializers.StringRelatedField(many=True, source='profesores_aptos', read_only=True)

    class Meta:
        model = Materia
        fields = '__all__'


class AulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aula
        fields = '__all__'


class RestriccionSerializer(serializers.ModelSerializer):
    profesor_info = serializers.StringRelatedField(source='profesor', read_only=True)
    aula_info = serializers.StringRelatedField(source='aula', read_only=True)
    materia_info = serializers.StringRelatedField(source='materia', read_only=True)

    class Meta:
        model = Restriccion
        fields = '__all__'
        read_only_fields = ['profesor_info', 'aula_info', 'materia_info']


class HorarioSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.StringRelatedField(source='profesor', read_only=True)
    materia_nombre = serializers.StringRelatedField(source='materia', read_only=True)
    aula_codigo = serializers.StringRelatedField(source='aula', read_only=True)

    class Meta:
        model = Horario
        fields = '__all__'
        read_only_fields = [
            'profesor_nombre',
            'materia_nombre',
            'aula_codigo'
        ]

# --- NUEVOS SERIALIZADORES ---

class SolicitudClaseSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.StringRelatedField(source='materia', read_only=True)
    profesor_nombre = serializers.StringRelatedField(source='profesor', read_only=True)
    aula_codigo = serializers.StringRelatedField(source='aula', read_only=True)

    class Meta:
        model = SolicitudClase
        fields = '__all__'
        read_only_fields = ['id', 'estado', 'materia_nombre', 'profesor_nombre', 'aula_codigo']


class VersionHorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionHorario
        fields = '__all__'
        read_only_fields = ['id', 'fecha_guardado']