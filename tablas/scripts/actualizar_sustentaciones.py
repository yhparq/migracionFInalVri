import psycopg2
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection, get_mysql_pilar3_connection, get_mysql_absmain_connection

def insertar_actas_de_sustentacion():
    """
    Inserta nuevos registros en tbl_dictamenes_info para las actas de sustentación (tipo_acta = 3).
    Este script lee cada sustentación de 'tesSustens' (MySQL), recolecta toda la información
    del trámite asociado y crea un registro completo y nuevo en PostgreSQL.
    """
    print("--- Iniciando inserción de actas de sustentación (tipo_acta = 3) ---")
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

        mysql_cur_pilar3.execute("SELECT Id, Codigo, IdTesista1, IdTesista2, IdJurado1, IdJurado2, IdJurado3, IdJurado4, IdJurado5 FROM tesTramites")
        tes_tramites_map = {row['Id']: row for row in mysql_cur_pilar3.fetchall()}
        
        mysql_cur_pilar3.execute("SELECT Id, IdCarrera, idEspec FROM tblTesistas")
        tesistas_academic_map = {row['Id']: {'IdCarrera': row['IdCarrera'], 'idEspec': row['idEspec']} for row in mysql_cur_pilar3.fetchall()}

        mysql_cur_absmain.execute("SELECT Id, Nombre, Titulo FROM dicCarreras")
        carreras_info_map = {row['Id']: {'Nombre': row['Nombre'], 'Titulo': row['Titulo']} for row in mysql_cur_absmain.fetchall()}

        mysql_cur_absmain.execute("SELECT Id, Denominacion FROM dicEspecialis")
        especialis_denominacion_map = {row['Id']: row['Denominacion'] for row in mysql_cur_absmain.fetchall()}

        mysql_cur_pilar3.execute("SELECT IdTramite, Titulo FROM tesTramsDet WHERE Titulo IS NOT NULL AND Titulo != '' GROUP BY IdTramite, Titulo")
        titulos_map = {row['IdTramite']: row['Titulo'] for row in mysql_cur_pilar3.fetchall()}

        print("  Paso 2: Obteniendo datos de sustentación desde MySQL (tesSustens)...")
        mysql_cur_pilar3.execute("SELECT Id, IdTramite, Fecha, Lugar FROM tesSustens")
        source_sustentaciones = mysql_cur_pilar3.fetchall()
        print(f"  Se encontraron {len(source_sustentaciones)} registros de sustentación para procesar.")

        print("  Paso 3: Procesando y preparando nuevos registros para insertar...")
        records_to_insert = []
        omitted_count = 0
        
        for sus in source_sustentaciones:
            id_tramite_antiguo = sus['IdTramite']
            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                omitted_count += 1
                continue

            tramite_info = tes_tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                omitted_count += 1
                continue

            def get_user_name(id_antiguo, map_type):
                if not id_antiguo or id_antiguo == 0: return None
                new_id = docentes_map.get(id_antiguo) if map_type == 'docente' else tesistas_map.get(id_antiguo)
                if not new_id: return 'N/A'
                return usuarios_map.get(new_id, 'N/A')

            presidente = get_user_name(tramite_info.get('IdJurado1'), 'docente')
            primer_miembro = get_user_name(tramite_info.get('IdJurado2'), 'docente')
            segundo_miembro = get_user_name(tramite_info.get('IdJurado3'), 'docente')
            asesor = get_user_name(tramite_info.get('IdJurado4'), 'docente')
            coasesor = get_user_name(tramite_info.get('IdJurado5'), 'docente')
            tesista1 = get_user_name(tramite_info.get('IdTesista1'), 'tesista')
            tesista2 = get_user_name(tramite_info.get('IdTesista2'), 'tesista')
            
            id_tesista1_antiguo = tramite_info.get('IdTesista1')
            tesista_academico_info = tesistas_academic_map.get(id_tesista1_antiguo)
            
            escuela_profesional = "Escuela no encontrada"
            denominacion_final = "Denominación no encontrada"

            if tesista_academico_info:
                id_carrera = tesista_academico_info['IdCarrera']
                id_especialidad = tesista_academico_info['idEspec']
                carrera_info = carreras_info_map.get(id_carrera)
                if carrera_info:
                    escuela_profesional = carrera_info.get('Nombre', escuela_profesional)
                if id_especialidad == 0:
                    if carrera_info:
                        denominacion_final = carrera_info.get('Titulo', "Título no encontrado")
                else:
                    denominacion_final = especialis_denominacion_map.get(id_especialidad, "Denominación de especialidad no encontrada")

            titulo = titulos_map.get(id_tramite_antiguo, 'Título no encontrado')

            record = (
                new_tramite_id, tramite_info.get('Codigo'), 30, # tipo_aprobacion = 30 (Aprobado)
                titulo, denominacion_final, tesista1, tesista2,
                escuela_profesional,
                presidente, primer_miembro, segundo_miembro, asesor,
                coasesor, None, None, 1, 3, # coasesor, fecha_dictamen=NULL, token=NULL, estado=1, tipo_acta=3
                sus.get('Id'), sus.get('Fecha'), sus.get('Lugar') # folio, fecha_sustentacion, lugar_sustentacion
            )
            records_to_insert.append(record)

        print(f"\n  Resumen del procesamiento: {len(records_to_insert)} preparados para inserción, {omitted_count} omitidos.")

        if records_to_insert:
            print("  Paso 4: Insertando datos en tbl_dictamenes_info...")
            insert_query = """
                INSERT INTO tbl_dictamenes_info (
                    id_tramite, codigo_proyecto, tipo_aprobacion, titulo, denominacion, tesista1, tesista2,
                    escuela_profesional, presidente, primer_miembro, segundo_miembro, asesor,
                    coasesor, fecha_dictamen, token, estado, tipo_acta, 
                    folio, fecha_sustentacion, lugar_sustentacion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {pg_cur.rowcount} nuevos registros de actas de sustentación.")

        print("--- Migración de actas de sustentación para tbl_dictamenes_info completada. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de actas de sustentación: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if pg_conn: pg_conn.close()
        if mysql_conn_pilar3: mysql_conn_pilar3.close()
        if mysql_conn_absmain: mysql_conn_absmain.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    insertar_actas_de_sustentacion()
