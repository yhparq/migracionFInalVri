import psycopg2
import sys
import os
import io
import csv
from db_connections import get_postgres_connection, get_mysql_pilar3_connection, get_mysql_absmain_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_dictamenes_info():
    """
    VERSIÓN MEJORADA Y OPTIMIZADA: Puebla tbl_dictamenes_info usando COPY.
    - Consolida datos de múltiples fuentes.
    - Mapea tipo_aprobacion a un INTEGER.
    - Utiliza carga masiva para un rendimiento superior.
    """
    print("--- Iniciando migración OPTIMIZADA para tbl_dictamenes_info (COPY) ---")
    pg_conn = None
    mysql_conn_pilar3 = None
    mysql_conn_absmain = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn_pilar3 = get_mysql_pilar3_connection()
        mysql_conn_absmain = get_mysql_absmain_connection()

        if not all([pg_conn, mysql_conn_pilar3, mysql_conn_absmain]):
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur_pilar3 = mysql_conn_pilar3.cursor(dictionary=True)
        mysql_cur_absmain = mysql_conn_absmain.cursor(dictionary=True)

        print("  Paso 1: Creando mapas de traducción y búsqueda...")
        
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docentes_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, CONCAT(nombres, ' ', apellidos) as full_name FROM tbl_usuarios")
        usuarios_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id_antiguo, id_usuario FROM tbl_tesistas WHERE id_antiguo IS NOT NULL")
        tesistas_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        mysql_cur_pilar3.execute("SELECT Id, Codigo, IdTesista1, IdTesista2, IdJurado1, IdJurado2, IdJurado3, IdJurado4 FROM tesTramites")
        tes_tramites_map = {row['Id']: row for row in mysql_cur_pilar3.fetchall()}
        
        mysql_cur_pilar3.execute("SELECT Id, IdCarrera, idEspec FROM tblTesistas")
        tesistas_academic_map = {row['Id']: {'IdCarrera': row['IdCarrera'], 'idEspec': row['idEspec']} for row in mysql_cur_pilar3.fetchall()}

        mysql_cur_absmain.execute("SELECT Id, Nombre, Titulo FROM dicCarreras")
        carreras_info_map = {row['Id']: {'Nombre': row['Nombre'], 'Titulo': row['Titulo']} for row in mysql_cur_absmain.fetchall()}

        mysql_cur_absmain.execute("SELECT Id, Denominacion FROM dicEspecialis")
        especialis_denominacion_map = {row['Id']: row['Denominacion'] for row in mysql_cur_absmain.fetchall()}

        print("  Mapeos completados.")

        print("  Paso 2: Obteniendo dictámenes de Iteración 3 desde MySQL...")
        mysql_cur_pilar3.execute("SELECT Id, IdTramite, Titulo, vb1, vb2, vb3, Fecha FROM tesTramsDet WHERE Iteracion = 3")
        source_dictamenes = mysql_cur_pilar3.fetchall()
        total_source = len(source_dictamenes)
        print(f"  Se encontraron {total_source} dictámenes para procesar.")

        print("  Paso 3: Identificando el dictamen más reciente por trámite...")
        latest_dates = {}
        for det in source_dictamenes:
            id_tramite = det['IdTramite']
            fecha = det.get('Fecha')
            if fecha:
                if id_tramite not in latest_dates or fecha > latest_dates[id_tramite]:
                    latest_dates[id_tramite] = fecha
        print(f"  Se identificaron las fechas más recientes para {len(latest_dates)} trámites.")

        print("  Paso 4: Procesando y transformando datos con la lógica de estado correcta...")
        records_to_insert = []
        omitted_count = 0
        
        for idx, det in enumerate(source_dictamenes):
            id_tramite_antiguo = det['IdTramite']
            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                omitted_count += 1
                continue

            tramite_info = tes_tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                omitted_count += 1
                continue

            def get_user_name_from_docente(id_jurado_antiguo):
                if not id_jurado_antiguo: return 'N/A'
                new_docente_id = docentes_map.get(id_jurado_antiguo)
                return usuarios_map.get(new_docente_id, 'N/A') if new_docente_id else 'N/A'

            presidente = get_user_name_from_docente(tramite_info.get('IdJurado1'))
            primer_miembro = get_user_name_from_docente(tramite_info.get('IdJurado2'))
            segundo_miembro = get_user_name_from_docente(tramite_info.get('IdJurado3'))
            asesor = get_user_name_from_docente(tramite_info.get('IdJurado4'))

            def get_user_name_from_tesista(id_tesista_antiguo):
                if not id_tesista_antiguo: return None
                id_usuario_nuevo = tesistas_map.get(id_tesista_antiguo)
                return usuarios_map.get(id_usuario_nuevo, 'N/A') if id_usuario_nuevo else 'N/A'

            tesista1 = get_user_name_from_tesista(tramite_info.get('IdTesista1'))
            tesista2 = get_user_name_from_tesista(tramite_info.get('IdTesista2'))

            id_tesista1_antiguo = tramite_info.get('IdTesista1')
            tesista_academico_info = tesistas_academic_map.get(id_tesista1_antiguo)
            
            escuela_profesional = "Escuela no encontrada"
            denominacion_final = "Denominación no encontrada"

            if tesista_academico_info:
                carrera_info = carreras_info_map.get(tesista_academico_info['IdCarrera'])
                if carrera_info:
                    escuela_profesional = carrera_info.get('Nombre', escuela_profesional)
                
                if tesista_academico_info['idEspec'] == 0:
                    if carrera_info:
                        denominacion_final = carrera_info.get('Titulo', "Título no encontrado")
                else:
                    denominacion_final = especialis_denominacion_map.get(tesista_academico_info['idEspec'], "Denominación de especialidad no encontrada")

            vb_sum = (det.get('vb1') or 0) + (det.get('vb2') or 0) + (det.get('vb3') or 0)
            if vb_sum == 3: tipo_aprobacion_id = 27
            elif vb_sum == 2: tipo_aprobacion_id = 26
            else: tipo_aprobacion_id = 28
            
            # Lógica de estado: 1 si es el más reciente, 0 si no lo es.
            is_latest = (det.get('Fecha') == latest_dates.get(id_tramite_antiguo))
            estado = 1 if is_latest else 0

            records_to_insert.append((
                new_tramite_id, tramite_info.get('Codigo'), tipo_aprobacion_id,
                det.get('Titulo'), denominacion_final, tesista1, tesista2, escuela_profesional,
                presidente, primer_miembro, segundo_miembro, asesor,
                None, det.get('Fecha'), None, estado, 1, None
            ))

        print(f"\n  Resumen del procesamiento: {total_source} registros leídos, {len(records_to_insert)} preparados para inserción, {omitted_count} omitidos.")

        if records_to_insert:
            print("  Paso 5: Cargando datos en tbl_dictamenes_info con COPY...")
            
            buffer = io.StringIO()
            for record in records_to_insert:
                # Limpiar tabs y newlines de cada item antes de unir
                clean_record = [str(item).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ') if item is not None else '\\N' for item in record]
                line = '\t'.join(clean_record)
                buffer.write(line + '\n')
            buffer.seek(0)

            columns = (
                'id_tramite', 'codigo_proyecto', 'tipo_aprobacion', 'titulo', 'denominacion', 'tesista1', 'tesista2',
                'escuela_profesional', 'presidente', 'primer_miembro', 'segundo_miembro', 'asesor',
                'coasesor', 'fecha_dictamen', 'token', 'estado', 'tipo_acta', 'folio'
            )
            
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_dictamenes_info ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')",
                file=buffer
            )
            
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {len(records_to_insert)} registros.")

        print("--- Migración de tbl_dictamenes_info completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de tbl_dictamenes_info: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if pg_conn: pg_conn.close()
        if mysql_conn_pilar3: mysql_conn_pilar3.close()
        if mysql_conn_absmain: mysql_conn_absmain.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_dictamenes_info()