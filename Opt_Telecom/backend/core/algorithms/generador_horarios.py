# backend/core/algorithms/generador_horarios.py

from core.models import Profesor, Materia, Aula, Horario, Restriccion
from django.db import transaction
from datetime import time, timedelta, datetime, date
import random
import json

# Función auxiliar para verificar disponibilidad del slot de tiempo en general
def is_time_slot_available(dia, hora_inicio, hora_fin, profesor=None, aula=None, current_generated_horarios=None):
    """
    Verifica si un slot de tiempo está disponible para un profesor y/o aula.
    Considera si ya hay un Horario asignado que se solape (en current_generated_horarios).
    """
    if current_generated_horarios is None:
        current_generated_horarios = []

    # Verificar horarios que ya se han generado en esta misma ejecución (aún no en DB)
    for h in current_generated_horarios:
        if h.dia == dia:
            # Comprobar solapamiento de tiempo (intervalos abiertos en el final)
            # h.hora_inicio < hora_fin AND h.hora_fin > hora_inicio
            if h.hora_inicio < hora_fin and h.hora_fin > hora_inicio:
                if profesor and h.profesor == profesor:
                    return False # Profesor ya ocupado en esta ejecución
                if aula and h.aula == aula:
                    return False # Aula ya ocupada en esta ejecución

    return True

# Función auxiliar para validar la disponibilidad definida del profesor (JSONField)
def validate_profesor_availability(profesor, dia, hora_inicio, hora_fin):
    """
    Verifica si un profesor está disponible en el slot de tiempo especificado,
    basándose en su campo 'disponibilidad' (JSONField).
    Formato esperado: {"DIA": ["HH:MM-HH:MM", ...]}
    """
    if not profesor.disponibilidad:
        return True # Si no hay disponibilidad definida, asumimos que está disponible

    try:
        # Asegurarse de que disponibilidad_profesor sea un diccionario
        if isinstance(profesor.disponibilidad, str):
            disponibilidad_profesor = json.loads(profesor.disponibilidad)
        else:
            disponibilidad_profesor = profesor.disponibilidad

        if dia not in disponibilidad_profesor:
            return False # El profesor no está disponible ese día según su definición

        franjas_disponibles_dia = disponibilidad_profesor[dia]

        # Convertir hora_inicio y hora_fin a objetos time para comparación
        start_time_slot = hora_inicio
        end_time_slot = hora_fin

        for franja_str in franjas_disponibles_dia:
            try:
                # Asumiendo formato "HH:MM-HH:MM"
                franja_inicio_str, franja_fin_str = franja_str.split('-')
                franja_inicio = time.fromisoformat(franja_inicio_str)
                franja_fin = time.fromisoformat(franja_fin_str)

                # Comprobar si el slot propuesto está completamente dentro de alguna franja disponible del profesor
                # Importante: el final del slot propuesto debe ser <= al final de la franja.
                # Y el inicio del slot propuesto debe ser >= al inicio de la franja.
                if start_time_slot >= franja_inicio and end_time_slot <= franja_fin:
                    return True # El slot propuesto está dentro de una franja disponible
            except ValueError:
                print(f"Advertencia: Formato de franja de disponibilidad incorrecto para {profesor.nombre}: '{franja_str}'. Ignorando esta franja.")
                continue # Saltar a la siguiente franja si el formato es erróneo

        return False # El slot propuesto no encaja en ninguna franja disponible para el día
    except (TypeError, json.JSONDecodeError, KeyError) as e:
        print(f"Error al procesar la disponibilidad de {profesor.nombre}: {e} (Disponibilidad: {profesor.disponibilidad}). Asumiendo no disponible.")
        return False # Si hay un error al leer la disponibilidad, asumimos no disponible por seguridad


# --- NUEVA FUNCIÓN: Validar requisitos de aula ---
def validate_aula_requirements(aula, requisitos_aula_materia):
    """
    Verifica si un aula cumple con los requisitos específicos de la materia (tipo_aula, recursos_minimos).
    """
    if not requisitos_aula_materia:
        return True # Si la materia no tiene requisitos de aula, cualquier aula es válida.

    try:
        # Asegurarse de que requisitos_aula_materia sea un diccionario
        if isinstance(requisitos_aula_materia, str):
            reqs = json.loads(requisitos_aula_materia)
        else:
            reqs = requisitos_aula_materia

        required_type = reqs.get("tipo_aula")
        required_resources = reqs.get("recursos_minimos", [])

        # Verificar tipo de aula
        if required_type and aula.tipo != required_type:
            return False

        # Verificar recursos mínimos (asumiendo que aula.recursos es una lista de strings)
        if required_resources:
            # Asegurarse de que aula.recursos sea una lista/iterable
            if isinstance(aula.recursos, str):
                aula_resources = json.loads(aula.recursos)
            else:
                aula_resources = aula.recursos or [] # Manejar None si el campo está vacío

            for res in required_resources:
                if res not in aula_resources:
                    return False # Falta un recurso requerido

        return True
    except (TypeError, json.JSONDecodeError, KeyError) as e:
        print(f"Advertencia: Error al procesar requisitos_de_aula de la materia: {e} (Requisitos: {requisitos_aula_materia}). Asumiendo aula no apta.")
        return False


# Función principal del algoritmo de generación de horarios
def generar_horarios_algoritmo():
    print("Iniciando la generación de horarios...")

    profesores = list(Profesor.objects.all())
    materias = list(Materia.objects.all())
    aulas = list(Aula.objects.all())
    # restricciones = list(Restriccion.objects.all()) # Para uso futuro

    if not profesores or not materias or not aulas:
        print("Faltan datos de profesores, materias o aulas para generar horarios. No se puede continuar.")
        return []

    horarios_generados = [] # Esta lista almacenará los objetos Horario antes de guardarlos en DB
    # Nuevo diccionario para llevar la cuenta de las horas asignadas a cada profesor
    horas_asignadas_a_profesor = {prof.id: 0 for prof in profesores} 

    # Limpiar horarios existentes en la base de datos antes de generar nuevos
    try:
        Horario.objects.all().delete()
        print("Horarios existentes borrados para regeneración.")
    except Exception as e:
        print(f"Error al borrar horarios existentes: {e}")


    # Definir bloques de tiempo disponibles por día (los mismos bloques de 2 horas)
    dias_semana = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']
    horas_dia = [time(h) for h in range(8, 18, 2)] # De 8 AM a 5 PM, en bloques de 2 horas (8, 10, 12, 14, 16)
    duracion_bloque = timedelta(hours=2) # Bloques de 2 horas

    # Crear todos los posibles bloques horarios (día, hora_inicio, hora_fin)
    bloques_disponibles_slots = []
    for dia in dias_semana:
        for hora_inicio_obj in horas_dia:
            hora_fin_obj = (datetime.combine(date.min, hora_inicio_obj) + duracion_bloque).time()
            if hora_fin_obj <= time(18): # Asegurar que la hora de fin no exceda las 18:00
                bloques_disponibles_slots.append({
                    'dia': dia,
                    'hora_inicio': hora_inicio_obj,
                    'hora_fin': hora_fin_obj
                })

    random.shuffle(bloques_disponibles_slots)

    # Ordenar materias por horas semanales requeridas (de más a menos)
    materias.sort(key=lambda x: x.horas_semanales, reverse=True)

    # Algoritmo de asignación
    for materia in materias:
        horas_asignadas_materia = {
            'Teoría': 0,
            'Práctica': 0,
            'Laboratorio': 0
        }
        # --- MODIFICACIÓN: Usar las horas requeridas de la materia por tipo de clase ---
        horas_requeridas_materia = {
            'Teoría': materia.horas_teoricas,
            'Práctica': materia.horarios_de_practicas,
            'Laboratorio': materia.horario_de_laboratorio
        }
        print(f"\n--- Intentando asignar horas para la materia: {materia.nombre} (Total: {materia.horas_semanales}h | Teoría: {horas_requeridas_materia['Teoría']}h, Práctica: {horas_requeridas_materia['Práctica']}h, Laboratorio: {horas_requeridas_materia['Laboratorio']}h) ---")

        # --- MODIFICACIÓN: Definir los tipos de clase en orden de prioridad ---
        tipos_clase_a_asignar = ['Teoría', 'Práctica', 'Laboratorio']
        
        for tipo_clase in tipos_clase_a_asignar:
            horas_necesarias_para_tipo = horas_requeridas_materia[tipo_clase]
            
            if horas_necesarias_para_tipo == 0:
                print(f"  INFO: No se requieren horas de {tipo_clase} para {materia.nombre}.")
                continue

            print(f"  Intentando asignar {horas_necesarias_para_tipo} horas de {tipo_clase} para {materia.nombre}...")

            # --- MODIFICACIÓN: Mezclar para evitar siempre el mismo orden ---
            random.shuffle(profesores)
            random.shuffle(aulas)
            random.shuffle(bloques_disponibles_slots)

            horas_asignadas_en_este_tipo = 0
            
            # Repetir búsqueda hasta asignar todas las horas de este tipo
            attempts = 0
            max_attempts = 100 * len(bloques_disponibles_slots) # Prevenir bucles infinitos

            while horas_asignadas_en_este_tipo < horas_necesarias_para_tipo and attempts < max_attempts:
                attempts += 1
                
                found_slot_for_type = False
                
                # Buscar slot dentro de los disponibles
                for slot in bloques_disponibles_slots:
                    # Calcular duración del slot
                    assigned_duration_current_slot = (slot['hora_fin'].hour - slot['hora_inicio'].hour)
                    
                    # Si el slot es más grande de lo que queda por asignar para este tipo de clase, intentamos asignarlo
                    # pero solo si es la última hora restante o si la materia no tiene un requisito de duración específico
                    if horas_asignadas_en_este_tipo + assigned_duration_current_slot > horas_necesarias_para_tipo and assigned_duration_current_slot != (horas_necesarias_para_tipo - horas_asignadas_en_este_tipo):
                        continue # Este bloque es demasiado grande para lo que queda por asignar en este tipo de clase, y no es el último bloque.

                    for profesor in profesores:
                        # Comprobar si el profesor puede dictar la materia
                        if materia.profesores_aptos.exists() and profesor not in materia.profesores_aptos.all():
                            continue

                        # Verificar carga horaria máxima del profesor
                        if (profesor.carga_horaria_maxima is not None and 
                            (horas_asignadas_a_profesor[profesor.id] + assigned_duration_current_slot) > profesor.carga_horaria_maxima):
                            # print(f"    INFO: Profesor {profesor.nombre} excedería su carga horaria máxima con este bloque.")
                            continue

                        # Comprobar la disponibilidad definida por el profesor (JSONField)
                        if not validate_profesor_availability(profesor, slot['dia'], slot['hora_inicio'], slot['hora_fin']):
                            continue

                        for aula in aulas:
                            # --- MODIFICACIÓN: Validar requisitos de aula para este tipo de clase ---
                            # Si es laboratorio, validar requisitos de aula. Para otros tipos, no es necesario.
                            if tipo_clase == 'Laboratorio' and not validate_aula_requirements(aula, materia.requisitos_de_aula):
                                # print(f"    INFO: Aula {aula.codigo} no cumple con requisitos de laboratorio para {materia.nombre}.")
                                continue
                            
                            # Verificar si el slot de tiempo ya está ocupado por otro horario generado
                            if not is_time_slot_available(slot['dia'], slot['hora_inicio'], slot['hora_fin'],
                                                          profesor=profesor, aula=aula,
                                                          current_generated_horarios=horarios_generados):
                                continue

                            # Si todo está OK, asignamos el horario
                            horario_propuesto = Horario(
                                profesor=profesor,
                                materia=materia,
                                aula=aula,
                                dia=slot['dia'],
                                hora_inicio=slot['hora_inicio'],
                                hora_fin=slot['hora_fin'],
                                tipo_clase=tipo_clase, # --- MODIFICACIÓN: Asignar tipo de clase
                                seccion="1", # Asumimos sección 1 por ahora, puedes generalizar esto si necesitas múltiples secciones
                                periodo_academico="2025-2", # Asumimos período académico fijo, puedes hacerlo dinámico
                                carrera_programa="ingeniero en sistemas" # Asumimos carrera fija, puedes hacerlo dinámico
                            )
                            horarios_generados.append(horario_propuesto)
                            
                            horas_asignadas_en_este_tipo += assigned_duration_current_slot
                            horas_asignadas_a_profesor[profesor.id] += assigned_duration_current_slot
                            
                            print(f"  Asignado: {tipo_clase} para {materia.nombre} | Prof: {profesor.nombre} | Aula: {aula.codigo} | Día: {slot['dia']} | Hora: {slot['hora_inicio']}-{slot['hora_fin']}")
                            print(f"    Horas de {tipo_clase} asignadas: {horas_asignadas_en_este_tipo} / {horas_necesarias_para_tipo}")
                            print(f"    Profesor {profesor.nombre} horas asignadas: {horas_asignadas_a_profesor[profesor.id]} / {profesor.carga_horaria_maxima}")
                            
                            found_slot_for_type = True
                            break # Salir del bucle de aulas
                        if found_slot_for_type:
                            break # Salir del bucle de profesores
                    if found_slot_for_type:
                        break # Salir del bucle de slots disponibles

                if not found_slot_for_type:
                    # Si no se encontró un slot en esta iteración, se incrementa attempts.
                    # Si llegamos aquí, es porque no se pudo encontrar un slot para el tipo de clase actual.
                    # Esto evita un bucle infinito si no hay slots.
                    print(f"    ADVERTENCIA: No se encontró un slot para {tipo_clase} de {materia.nombre} en este intento.")
                    # break # Si no se encontró un slot, podríamos romper aquí para no seguir intentando para este tipo de clase.
                    # Sin embargo, el while loop con max_attempts se encargará de esto.

            if horas_asignadas_en_este_tipo < horas_necesarias_para_tipo:
                print(f"  ADVERTENCIA: No se pudo asignar todas las horas de {tipo_clase} para {materia.nombre}. Faltan {horas_necesarias_para_tipo - horas_asignadas_en_este_tipo} horas.")
            else:
                print(f"  Horas de {tipo_clase} para {materia.nombre} completadas con {horas_asignadas_en_este_tipo} horas.")

        # Verificar si todas las horas totales de la materia fueron asignadas
        total_horas_asignadas_materia = sum(horas_asignadas_materia.values()) # Esto no se está usando bien.
        # Mejor verificar directamente si todas las horas requeridas por tipo fueron asignadas.
        
        # Una vez que salimos del bucle de tipos de clase, podemos verificar el total.
        total_horas_requeridas = sum(horas_requeridas_materia.values())
        total_horas_realmente_asignadas = sum(h.hora_fin.hour - h.hora_inicio.hour for h in horarios_generados if h.materia == materia)

        if total_horas_realmente_asignadas < total_horas_requeridas:
             print(f"  ADVERTENCIA FINAL: No se pudo asignar todas las horas para {materia.nombre}. Faltan {total_horas_requeridas - total_horas_realmente_asignadas} horas en total.")
        else:
             print(f"  {materia.nombre} asignada completamente con {total_horas_realmente_asignadas} horas en total.")

    try:
        with transaction.atomic():
            for horario in horarios_generados:
                horario.save()
        print(f"\n--- Generación de horarios completada. Se crearon {len(horarios_generados)} horarios. ---")
        return horarios_generados
    except Exception as e:
        print(f"\n--- ERROR CRÍTICO al guardar horarios en la base de datos: {e} ---")
        try:
            Horario.objects.all().delete()
            print("Horarios existentes borrados tras error de guardado para asegurar un estado limpio.")
        except Exception as delete_e:
            print(f"Error adicional al intentar limpiar horarios después del fallo: {delete_e}")
        raise