import sys
import os
import re
from io import StringIO
from datetime import datetime
from collections import defaultdict

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def normalize_action_name(name):
    """Normaliza el nombre de una acción para facilitar el mapeo."""
    if not isinstance(name, str):
        return ''
    return ' '.join(name.strip().lower().split())

# Diccionario de mapeo explícito para acciones inconsistentes (VERSIÓN CORREGIDA Y AMPLIADA)
ACCION_MAP = {
    # Mapeos Originales (Corregidos)
    'acepta ser asesor/director de proyecto': 'acepta ser asesor/director de proyecto',
    'aceptación de director': 'acepta ser asesor/director de proyecto',
    'aceptación del director': 'acepta ser asesor/director de proyecto',
    'agregar tesista a proyecyto': 'agregar tesista',
    'agrega tesista': 'agregar tesista',
    'agregar tesista a proyecto': 'agregar tesista',
    'ampliación de proyecto de tesis': 'ampliación de proyecto de tesis',
    'anulación de proyecto': 'anulacion de proyecto de tesis',
    'anulación de proyecto de tesis': 'anulacion de proyecto de tesis',
    'exceso de tiempo director/asesor': 'archivamiento de proyecto por exceso de tiempo director',
    'cambio de asesor': 'cambio de asesor/director',
    'cambio de director': 'cambio de asesor/director',
    'cambio de estado de dictamen': 'cambio de estado de dictamen',
    'cambio de jurado': 'cambio de jurado',
    'cambio jurado': 'cambio de jurado',
    'cambio de jurado pre-sustentación': 'cambio de jurado',
    'cambio de jurado y envió de borrador': 'cambio de jurado',
    'cambio de jurado borrador': 'cambio de jurado',
    'cambio de jurados borrador': 'cambio de jurado',
    'cambio de jurado de proyecto': 'cambio de jurado',
    'cambio de jurado proyecto': 'cambio de jurado',
    'cambio de': 'correcion de estado', # Demasiado ambiguo, se asigna a corrección general
    'cambio de jurado (f)': 'cambio de jurado',
    'cambio de jurado 2': 'cambio de jurado',
    'cambio de jurado -': 'cambio de jurado',
    'cambio de jurada': 'cambio de jurado',
    'cambio de jurado por licencia': 'cambio de jurado',
    'cambio de jurado presidente por cargo': 'cambio de jurado',
    'cambio de jurado de borrador': 'cambio de jurado',
    'cambio de linea': 'cambio de linea de investigacion',
    'cambio de nombre': 'cambio de nombre de tesista',
    'cambio de titulo de proyecto de tesis': 'cambio de titulo de proyecto de tesis',
    'cambio de nombre titulo de proyecto': 'cambio de titulo de proyecto de tesis',
    'cambio de título': 'cambio de titulo de proyecto de tesis',
    'cambio de titulo': 'cambio de titulo de proyecto de tesis',
    'corrección de titulo de borrador': 'cambio de titulo de tesis',
    'cambio de titulo de borrador de tesis': 'cambio de titulo de tesis',
    'cancelar proyecto de tesis': 'cancelacion de proyecto',
    'cancelación de proyecto de tesis': 'cancelacion de proyecto',
    'cancelación de proyecto': 'cancelacion de proyecto',
    'desaparobacion de proyecto y cancelación': 'cancelación de proyecto por desaprobación',
    'cancelación de proyecto por desaprobación': 'cancelación de proyecto por desaprobación',
    'cancelación por desaprobación de proyecto': 'cancelación de proyecto por desaprobación',
    'cancelación por desaprobación': 'cancelación de proyecto por desaprobación',
    'cancelación de proyecto de tesis por desaprobación': 'cancelación de proyecto por desaprobación',
    'detalle habilitación borrador': 'carga de requisitos para habilitacion etapa borrador',
    'subida de bachiller': 'carga de requisitos para habilitacion etapa borrador',
    'correccion por error en bd': 'correcion de estado',
    'corrección de orden de jurado': 'correcion de estado',
    'corrección estado': 'correcion de estado',
    'cambio de orden de jurado': 'correcion de estado',
    'corrección de formato borrador': 'correcion de formato borrador',
    'corrección fecha acta de sustentación': 'correcion fecha acta de sustentacion',
    'docente renuncia a proyecto de tesis': 'docente renuncia a tesis',
    'docente renuncia a borrador de tesis': 'docente renuncia a tesis',
    'elminación de trámite': 'eliminacion de un tesista',
    'eliminación de un tesista de un proyecto': 'eliminacion de un tesista',
    'retirar un tesista': 'eliminacion de un tesista',
    'renuncia de un integrante': 'eliminacion de un tesista',
    'renuncia de tesista': 'eliminacion de un tesista',
    'habilitación de subida de correcciones': 'habilitacion de tramite para carga de correciones',
    'habitacion': 'habilitacion de tramite para carga de correciones',
    'habilitacion subir correcciones': 'habilitacion de tramite para carga de correciones',
    'habilitacion de subida': 'habilitacion de tramite para carga de correciones',
    'habilitacion de correcciones': 'habilitacion de tramite para carga de correciones',
    'habilitación de subida': 'habilitacion de tramite para carga de correciones',
    'habilitación excepcional r.r. n° 2965': 'habilitacion excepcional',
    'bloqueo del proyecto por plagio': 'inhabilitacion de tesis por plagio',
    'recepción de ejemplares': 'recepcion de ejemplares de borrador de tesis',
    'rechazo del director': 'rechazo del proyecto por el director',
    'reconformación de jurado': 'reconformación de jurado',
    'reconformación jurados': 'reconformación de jurado',
    'renuncia al proyecto': 'renuncia a tramite',
    'renuncia a proyecto de tesis': 'renuncia a tramite',
    'renuncia de proyecto de tesis': 'renuncia a tramite',
    'renuncia a proyecto y borrador de tesis': 'renuncia a tramite',
    'renuncia a proyecto de tesis de un tesista': 'renuncia a tramite',
    'renuncia a borrador de tesis': 'renuncia a tramite',
    'reprogramacion de sustentación': 'reprogramacion de fecha de sustentacion',
    'reprogramación sustentación': 'reprogramacion de fecha de sustentacion',
    'recuperación trámite': 'restablecimiento de tramite',
    'reactivación de trámite': 'restablecimiento de tramite',
    'reestablecimiento sorteo': 'restablecimiento de tramite',
    'trámite desarchivado': 'restablecimiento de tramite',
    'retiro coasesor': 'retiro de coasesor externo',
    'retiro de co asesor': 'retiro de coasesor externo',
    'retorna proyecto : corregir formato': 'retorna proyecto',
    'retorna documento : corregir formato': 'retorna proyecto',
    'retrocede estado': 'retrocede estado',
    'retroce estado': 'retrocede estado',
    'retroceso estado': 'retrocede estado',
    'retroceso de estado': 'retrocede estado',
    'retrocede a estado 11': 'retrocede estado',
    'solicitud no presencial': 'solicitud de sustentacion no presencial',
    'proyecto de tesis archivado': 'tramite archivado por exceso de tiempos de ejecucion',
    'trámite archivado': 'tramite archivado por exceso de tiempos de ejecucion',
    'proyecto con tiempo excedido': 'tramite archivado por exceso de tiempos de ejecucion',
    'revision de formato y envio': 'corrección de formato de proyecto de tesis',
    
    # Nuevos Mapeos de la Lista de Errores
    'aprobación de proyecto': 'proyecto aprobado por director/asesor',
    'desaprobación de proyecto': 'proyecto desaprobado/enviado para corregir por asesor',
    'dictaminación de jurado 1': 'cambio de estado de dictamen',
    'dictaminación de jurado 1 - r': 'cambio de estado de dictamen',
    'dictaminación de jurado 1 : 0': 'cambio de estado de dictamen',
    'dictaminación de jurado 1 : 1': 'cambio de estado de dictamen',
    'dictaminación de jurado 1 : 2': 'cambio de estado de dictamen',
    'dictaminación de jurado 2': 'cambio de estado de dictamen',
    'dictaminación de jurado 2 : 0': 'cambio de estado de dictamen',
    'dictaminación de jurado 2 : 1': 'cambio de estado de dictamen',
    'dictaminación de jurado 2 : 2': 'cambio de estado de dictamen',
    'dictaminación de jurado 3': 'cambio de estado de dictamen',
    'dictaminación de jurado 3 : 0': 'cambio de estado de dictamen',
    'dictaminación de jurado 3 : 1': 'cambio de estado de dictamen',
    'dictaminación de jurado 3 : 2': 'cambio de estado de dictamen',
    'dictaminación de jurado 4': 'cambio de estado de dictamen',
    'dictaminación de jurado 4 : 0': 'cambio de estado de dictamen',
    'dictaminación de jurado 4 : 1': 'cambio de estado de dictamen',
    'dictaminación de jurado 4 : 2': 'cambio de estado de dictamen',
    'enviado al director': 'proyecto aprobado por sub/director', # Asumiendo que es un paso de aprobación
    'envio a dictaminacion de borrador': 'inicio de etapa 12',
    'envio a director': 'proyecto aprobado por sub/director',
    'fecha de sustentacion': 'publicar sustentación',
    'fin de correcciones borrador jurado 1': 'jurados finalizan correcion',
    'fin de correcciones borrador jurado 2': 'jurados finalizan correcion',
    'fin de correcciones borrador jurado 2 /chdeanby1m': 'jurados finalizan correcion',
    'fin de correcciones borrador jurado 3': 'jurados finalizan correcion',
    'fin de correcciones borrador jurado 4': 'jurados finalizan correcion',
    'fin de correcciones jurado 1': 'jurados finalizan correcion',
    'fin de correcciones jurado 2': 'jurados finalizan correcion',
    'fin de correcciones jurado 3': 'jurados finalizan correcion',
    'fin de correcciones jurado 4': 'jurados finalizan correcion',
    'habilitacion de proyecto': 'restablecimiento de tramite',
    'modificacion de integrantes': 'agregar tesista', # Se asimila a agregar/quitar
    'modificación de acta y renuncia de integrante': 'eliminacion de un tesista',
    'proyecto enviado a revisión': 'sorteo de jurados',
    'registro dictamen': 'cambio de estado de dictamen',
    'reincorporación a proyecto': 'agregar tesista',
    'renuncia de jurado a proyecto aprobado': 'cambio de jurado',
    'sorteo e inicio de revision': 'sorteo de jurados',
    'subida de borrador': 'culminación etapa 10',
    'subida de borrador final': 'culminación etapa 10',
    'subida de corrección': 'envio de correciones a los jurados',
    'subida de proyecto': 'culminación de etapa 1',
    'visto bueno': 'formato de proyecto aprobado',
    'registro de dictamen': 'cambio de estado de dictamen',
    # Acciones a ignorar o que son demasiado ambiguas se mapean a corrección general
    'cam': 'correcion de estado',
    'cancelación de cambio': 'correcion de estado',
    'deshabilitado': 'correcion de estado',
    'elimina estado 5': 'correcion de estado',
    'espera - retrocede': 'correcion de estado',
    'habilita para dictamen': 'correcion de estado',
    'habilitación para nueva generación de acta': 'correcion de estado',
    'obsercación': 'correcion de estado',
    'retroceder y eliminar el proyecto': 'correcion de estado',
    'actualización proyecto de tesis': 'correcion de estado',
}

def sanitize_for_copy(value):
    if value is None: return r'\N'
    return str(value).replace('\\', '\\\\').replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')

def migrar_log_acciones():
    mysql_conn = None
    pg_conn = None
    try:
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        print("--- Iniciando migración de log de acciones (log_acciones) con mapeo mejorado ---")

        # 1. Cargar mapas de traducción
        print("INFO: Cargando mapas de traducción desde PostgreSQL...")
        
        pg_cur.execute("SELECT id, nombre, id_etapa_pertenencia FROM dic_acciones")
        acciones_data = pg_cur.fetchall()
        mapa_acciones = {normalize_action_name(row[1]): (row[0], row[2]) for row in acciones_data}
        
        accion_default_id = 92
        accion_default = next(( (row[0], row[2]) for row in acciones_data if row[0] == accion_default_id), None)
        if not accion_default: raise Exception(f"La acción por defecto con ID {accion_default_id} no se encontró.")
        print(f"INFO: Acción de respaldo configurada en ID {accion_default_id}.")

        pg_cur.execute("SELECT id_antiguo, id FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        mapa_tramites = dict(pg_cur.fetchall())

        pg_cur.execute("SELECT id, id_usuario FROM tbl_admins")
        mapa_admins = dict(pg_cur.fetchall())
        pg_cur.execute("SELECT id, id_usuario FROM tbl_docentes")
        mapa_docentes = dict(pg_cur.fetchall())
        pg_cur.execute("SELECT id, id_usuario FROM tbl_coordinadores")
        mapa_coordinadores = dict(pg_cur.fetchall())
        pg_cur.execute("SELECT id, id_usuario FROM tbl_tesistas")
        mapa_tesistas = dict(pg_cur.fetchall())

        # Mapa robusto para id_usuario_servicio
        pg_cur.execute("SELECT id, id_usuario, id_servicio FROM tbl_usuarios_servicios")
        mapa_servicios_por_usuario = defaultdict(list)
        for row in pg_cur.fetchall():
            mapa_servicios_por_usuario[row[1]].append({'id': row[0], 'id_servicio': row[2]})

        pg_cur.execute("SELECT id, nombre FROM dic_servicios")
        mapa_id_a_nombre_servicio = {row[0]: row[1].lower() for row in pg_cur.fetchall()}
        
        # Prioridades de roles para desambiguación
        prioridad_servicios_docente = ['asesor', 'jurado revisor', 'docente']
        
        # 2. Obtener registros de logTramites de MySQL
        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT IdTramite, Accion, Detalle, IdUser, Tipo, Fecha FROM logTramites")
        logs_antiguos = mysql_cur.fetchall()
        print(f"INFO: Se encontraron {len(logs_antiguos)} registros en logTramites.")

        log_records_to_insert = []
        registros_omitidos = 0
        servicios_no_encontrados = 0
        now_timestamp = datetime.now()

        # 3. Procesar cada registro del log
        for log in logs_antiguos:
            id_tramite_nuevo = mapa_tramites.get(log['IdTramite'])
            if not id_tramite_nuevo:
                registros_omitidos += 1
                continue

            id_usuario_nuevo = None
            id_user_antiguo = log['IdUser']
            tipo_usuario = log['Tipo']
            
            if id_user_antiguo == 0:
                id_usuario_nuevo = mapa_admins.get(7)
            elif tipo_usuario:
                if tipo_usuario.isdigit() or tipo_usuario in ('P', 'A'):
                    id_usuario_nuevo = mapa_admins.get(id_user_antiguo)
                elif tipo_usuario == 'D':
                    id_usuario_nuevo = mapa_docentes.get(id_user_antiguo)
                elif tipo_usuario == 'C':
                    id_usuario_nuevo = mapa_coordinadores.get(id_user_antiguo)
                elif tipo_usuario == 'T':
                    id_usuario_nuevo = mapa_tesistas.get(id_user_antiguo)
            
            if id_usuario_nuevo is None:
                registros_omitidos += 1
                continue

            # Lógica robusta para encontrar id_usuario_servicio
            id_usuario_servicio_nuevo = None
            servicios_del_usuario = mapa_servicios_por_usuario.get(id_usuario_nuevo)
            
            if servicios_del_usuario:
                if tipo_usuario == 'D':
                    # Lógica de prioridad para docentes
                    for rol_prioritario in prioridad_servicios_docente:
                        for servicio in servicios_del_usuario:
                            if mapa_id_a_nombre_servicio.get(servicio['id_servicio']) == rol_prioritario:
                                id_usuario_servicio_nuevo = servicio['id']
                                break
                        if id_usuario_servicio_nuevo:
                            break
                    if not id_usuario_servicio_nuevo: # Si no coincide ninguno prioritario, tomar el primero
                        id_usuario_servicio_nuevo = servicios_del_usuario[0]['id']
                else:
                    # Para otros roles, tomar el primer servicio encontrado
                    id_usuario_servicio_nuevo = servicios_del_usuario[0]['id']

            if id_usuario_servicio_nuevo is None:
                servicios_no_encontrados += 1

            # Lógica de mapeo de acción
            nombre_accion_original = log['Accion']
            nombre_accion_norm = normalize_action_name(nombre_accion_original)
            nombre_accion_mapeado = ACCION_MAP.get(nombre_accion_norm, nombre_accion_norm)
            id_accion_nuevo, id_etapa_nueva = mapa_acciones.get(nombre_accion_mapeado, accion_default)
            
            fecha_a_insertar = log['Fecha'] or now_timestamp

            log_records_to_insert.append(
                (id_tramite_nuevo, id_accion_nuevo, id_etapa_nueva, id_usuario_nuevo, fecha_a_insertar, log['Detalle'] or 'Sin detalle.', id_usuario_servicio_nuevo)
            )

        print(f"INFO: Procesamiento finalizado. {len(log_records_to_insert)} registros serán migrados. {registros_omitidos} registros fueron omitidos.")
        if servicios_no_encontrados > 0:
            print(f"ADVERTENCIA: No se encontró una correspondencia en 'tbl_usuarios_servicios' para {servicios_no_encontrados} registros.")

        # 4. Inserción masiva
        if log_records_to_insert:
            print("\nINFO: Realizando inserción masiva en log_acciones...")
            pg_cur.execute("TRUNCATE TABLE public.log_acciones RESTART IDENTITY;")
            
            buffer = StringIO()
            for record in log_records_to_insert:
                sanitized_record = [sanitize_for_copy(field) for field in record]
                buffer.write('\t'.join(sanitized_record) + '\n')
            buffer.seek(0)
            
            pg_cur.copy_expert("COPY log_acciones(id_tramite, id_accion, id_etapa, id_usuario, fecha, mensaje, id_usuario_servicio) FROM STDIN", buffer)
            print(f"INFO: Se insertaron {pg_cur.rowcount} registros en log_acciones.")
        
        pg_conn.commit()
        print("\n--- Migración de log_acciones finalizada exitosamente. ---")

    except Exception as e:
        print(f"ERROR: Ocurrió un error crítico durante la migración de log_acciones: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if mysql_conn: mysql_conn.close()
        if pg_conn: pg_conn.close()

if __name__ == "__main__":
    migrar_log_acciones()
