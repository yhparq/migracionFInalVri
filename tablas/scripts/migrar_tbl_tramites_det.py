import psycopg2
import sys
import os
import io
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_tramites_det():
    """
    CORREGIDO v3: Migra los detalles de los trámites (vistos buenos de jurados).
    Esta versión garantiza que el id_tramite insertado en tbl_tramitesdet sea el
    nuevo ID secuencial de PostgreSQL, utilizando una cadena de mapeo correcta.
    """
    print("--- Iniciando migración CORREGIDA v3 de tbl_tramitesdet ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # 1. Mapa de traducción de trámites {id_antiguo: id_nuevo_serial}
        print("  Paso 1: Creando mapa de traducción para trámites...")
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}
        print(f"  Se mapearon {len(tramites_map)} trámites.")

        # 2. Mapa de búsqueda para jurados por ID NUEVO
        #    Clave: (id_tramite_NUEVO, id_orden) -> Valor: id_docente_NUEVO
        print("  Paso 2: Creando mapa de búsqueda para jurados por ID nuevo...")
        pg_cur.execute("SELECT id_tramite, orden, id_docente FROM tbl_conformacion_jurados")
        jurado_map = {(row[0], row[1]): row[2] for row in pg_cur.fetchall()}
        print(f"  Se mapearon {len(jurado_map)} jurados para búsqueda.")

        # 3. Mapa de fechas de corrección desde logTramites
        mysql_cur.execute("""
            SELECT IdTramite, MAX(Fecha) as fecha_correccion
            FROM logTramites
            WHERE Accion LIKE '%correcci_n%' OR Accion LIKE '%observaci_n%'
            GROUP BY IdTramite
        """)
        fechas_correccion_map = {row['IdTramite']: row['fecha_correccion'] for row in mysql_cur.fetchall()}

        # 4. Leer datos de origen de MySQL
        print("  Paso 3: Leyendo datos de origen desde tesTramsDet...")
        mysql_cur.execute("SELECT IdTramite, Iteracion, vb1, vb2, vb3, vb4, Fecha FROM tesTramsDet")
        source_data = mysql_cur.fetchall()
        print(f"  Se encontraron {len(source_data)} filas en tesTramsDet.")

        # 5. Procesar datos con la lógica corregida
        print("  Paso 4: Procesando y transformando datos...")
        data_for_copy = []
        unmatched_records = 0
        
        visto_bueno_rules = {
            1: {1: 2, 0: 1},
            2: {1: 3, -1: 6, 0: 12},
            3: {1: 3, -1: 6, 0: 12},
            4: {0: 7, 1: 8},
            5: {0: 13, 1: 9, 2: 11, -1: 10}
        }
        etapa_rules = {1: 6, 2: 7, 3: 7, 4: 12, 5: 15}

        for row in source_data:
            id_tramite_antiguo = row['IdTramite']
            # LÓGICA CLAVE: Traducir el ID antiguo al ID NUEVO y SERIAL
            new_serial_tramite_id = tramites_map.get(id_tramite_antiguo)

            if not new_serial_tramite_id:
                unmatched_records += 4
                continue

            iteracion = row['Iteracion']
            id_etapa = etapa_rules.get(iteracion)
            
            if not id_etapa:
                unmatched_records += 4
                continue

            for i in range(1, 5):
                orden_jurado = i
                visto_bueno_value = row.get(f'vb{i}')

                # LÓGICA CLAVE: Usar el ID NUEVO y SERIAL para buscar al docente
                new_docente_id = jurado_map.get((new_serial_tramite_id, orden_jurado))
                
                if new_docente_id is None:
                    unmatched_records += 1
                    continue

                id_visto_bueno = visto_bueno_rules.get(iteracion, {}).get(visto_bueno_value)
                if iteracion == 1 and id_visto_bueno is None:
                    id_visto_bueno = 1

                if id_visto_bueno is None:
                    unmatched_records += 1
                    continue
                
                fecha_registro = fechas_correccion_map.get(id_tramite_antiguo, row['Fecha'])

                data_for_copy.append((
                    new_serial_tramite_id, # <-- ASEGURADO: Este es el ID NUEVO y SERIAL
                    new_docente_id,
                    id_etapa,
                    id_visto_bueno,
                    fecha_registro,
                    orden_jurado,
                    1
                ))

        print(f"  Se prepararon {len(data_for_copy)} registros para la carga masiva.")
        if unmatched_records > 0:
            print(f"  Se ignoraron {unmatched_records} posibles registros por falta de mapeo.")

        # 6. Cargar los datos en PostgreSQL
        if data_for_copy:
            print("  Paso 5: Cargando datos en PostgreSQL con COPY...")
            buffer = io.StringIO()
            for record in data_for_copy:
                line = '\t'.join(map(lambda x: str(x).replace('\t', ' '), record))
                buffer.write(line + '\n')
            
            buffer.seek(0)
            
            columns = ('id_tramite', 'id_docente', 'id_etapa', 'id_visto_bueno', 
                       'fecha_registro', 'id_orden', 'estado')
            
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_tramitesdet ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '')",
                file=buffer
            )
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {len(data_for_copy)} registros en tbl_tramitesdet.")

        print("--- Migración CORREGIDA v3 de tbl_tramitesdet completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de tbl_tramitesdet: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_tramites_det()