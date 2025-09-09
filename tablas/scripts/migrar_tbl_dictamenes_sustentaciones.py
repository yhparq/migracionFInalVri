import psycopg2
import sys
import os
from db_connections import get_postgres_connection, get_mysql_pilar3_connection, get_mysql_absmain_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_dictamenes_sustentaciones():
    """
    Puebla tbl_dictamenes_info con datos de sustentaciones (tesSustenAct).
    - No borra registros existentes.
    - La lógica de aprobación se basa en el campo 'Obs'.
    - El folio se mapea desde el ID de tesSustenAct.
    - Lógica de denominación y escuela profesional corregida.
    """
    print("--- Iniciando migración de sustentaciones para poblar tbl_dictamenes_info (v2 CORREGIDA) ---")
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

        mysql_cur_pilar3.execute("SELECT IdTramite, Titulo FROM tesTramsDet WHERE Titulo IS NOT NULL AND Titulo != '' GROUP BY IdTramite, Titulo")
        titulos_map = {row['IdTramite']: row['Titulo'] for row in mysql_cur_pilar3.fetchall()}

        print(f"  Mapeos completados.")

        print("  Paso 2: Obteniendo datos de sustentaciones desde MySQL (tesSustenAct)...")
        mysql_cur_pilar3.execute("SELECT Id, IdTramite, Fecha, Obs FROM tesSustenAct")
        source_sustentaciones = mysql_cur_pilar3.fetchall()
        total_source = len(source_sustentaciones)
        print(f"  Se encontraron {total_source} registros de sustentación para procesar.")

        print("  Paso 3: Procesando y transformando datos...")
        records_to_insert = []
        omitted_count = 0
        
        for sus in source_sustentaciones:
            id_tramite_antiguo = sus['IdTramite']
            id_sustentacion_antiguo = sus['Id']

            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                omitted_count += 1
                continue

            tramite_info = tes_tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                omitted_count += 1
                continue

            obs_text = (sus.get('Obs') or "").strip().upper()
            tipo_aprobacion_id = None
            if "DESAPROBADO" in obs_text: tipo_aprobacion_id = 32
            elif obs_text == "APROBADO": tipo_aprobacion_id = 30
            elif "APROBADO" in obs_text: tipo_aprobacion_id = 31
            
            if tipo_aprobacion_id is None:
                omitted_count += 1
                continue

            def get_user_name(id_antiguo, map_type, role):
                if not id_antiguo: return 'N/A' if map_type == 'docente' else None
                new_id = docentes_map.get(id_antiguo) if map_type == 'docente' else tesistas_map.get(id_antiguo)
                if not new_id: return 'N/A'
                return usuarios_map.get(new_id, 'N/A')

            presidente = get_user_name(tramite_info.get('IdJurado1'), 'docente', 'Presidente')
            primer_miembro = get_user_name(tramite_info.get('IdJurado2'), 'docente', '1er Miembro')
            segundo_miembro = get_user_name(tramite_info.get('IdJurado3'), 'docente', '2do Miembro')
            asesor = get_user_name(tramite_info.get('IdJurado4'), 'docente', 'Asesor')
            tesista1 = get_user_name(tramite_info.get('IdTesista1'), 'tesista', 'Tesista 1')
            tesista2 = get_user_name(tramite_info.get('IdTesista2'), 'tesista', 'Tesista 2')
            
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
                new_tramite_id, tramite_info.get('Codigo'), tipo_aprobacion_id,
                titulo, denominacion_final, tesista1, tesista2,
                escuela_profesional,
                presidente, primer_miembro, segundo_miembro, asesor,
                None, sus.get('Fecha'), None, 1, 2, id_sustentacion_antiguo
            )
            records_to_insert.append(record)

        print(f"\n  Resumen del procesamiento: {total_source} registros leídos, {len(records_to_insert)} preparados para inserción, {omitted_count} omitidos.")

        if records_to_insert:
            print("  Paso 4: Insertando datos de sustentaciones en tbl_dictamenes_info...")
            insert_query = """
                INSERT INTO tbl_dictamenes_info (
                    id_tramite, codigo_proyecto, tipo_aprobacion, titulo, denominacion, tesista1, tesista2,
                    escuela_profesional, presidente, primer_miembro, segundo_miembro, asesor,
                    coasesor, fecha_dictamen, token, estado, tipo_acta, folio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {pg_cur.rowcount} registros nuevos.")

        print("--- Migración de sustentaciones para tbl_dictamenes_info completada. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de sustentaciones: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if pg_conn: pg_conn.close()
        if mysql_conn_pilar3: mysql_conn_pilar3.close()
        if mysql_conn_absmain: mysql_conn_absmain.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_dictamenes_sustentaciones()
