import psycopg2
import io
import sys
import os
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

# Ajuste del sys.path para permitir importaciones desde el directorio raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_conformacion_jurado_fast():
    """
    Migra la conformación INICIAL de jurados desde tesTramites (MySQL) a 
    tbl_conformacion_jurados (PostgreSQL) usando el método COPY.

    Primero, altera la tabla para permitir NULLs en columnas clave y luego
    realiza la migración de datos.
    """
    print("--- Iniciando migración de tbl_conformacion_jurado (Inicial, Método COPY) ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # PASO 1: Alterar la tabla para aceptar NULLs
        print("  Paso 1: Alterando la tabla tbl_conformacion_jurados para aceptar NULLs...")
        pg_cur.execute("ALTER TABLE public.tbl_conformacion_jurados ALTER COLUMN id_asignacion DROP NOT NULL;")
        pg_cur.execute("ALTER TABLE public.tbl_conformacion_jurados ALTER COLUMN fecha_asignacion DROP NOT NULL;")
        print("  Alteración completada.")

        # PASO 2: Crear mapas de IDs para trámites y docentes
        print("  Paso 2: Creando mapas de IDs desde PostgreSQL...")
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}
        
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docente_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id FROM tbl_usuarios WHERE correo = 'sistema@vriunap.pe'")
        system_user_id = pg_cur.fetchone()[0]
        print(f"  Mapeo completado: {len(tramites_map)} trámites, {len(docente_map)} docentes.")

        # PASO 3: Obtener datos de origen y procesarlos
        mysql_cur.execute("""
            SELECT IdTramite, MAX(Fecha) as fecha_asignacion
            FROM logTramites
            WHERE Accion = 'Proyecto enviado a Revisión'
            GROUP BY IdTramite
        """)
        fechas_asignacion = {row['IdTramite']: row['fecha_asignacion'] for row in mysql_cur.fetchall()}

        mysql_cur.execute("SELECT Id, IdJurado1, IdJurado2, IdJurado3, IdJurado4 FROM tesTramites")
        source_tramites = mysql_cur.fetchall()

        print("  Paso 3: Procesando y transformando datos...")
        data_for_copy = []
        jurado_fields = ['IdJurado1', 'IdJurado2', 'IdJurado3', 'IdJurado4']
        unmapped_jurados = 0

        for tramite in source_tramites:
            id_antiguo = tramite['Id']
            new_tramite_id = tramites_map.get(id_antiguo)
            fecha_asignacion = fechas_asignacion.get(id_antiguo)

            if not new_tramite_id:
                continue

            for i, field in enumerate(jurado_fields):
                old_docente_id = tramite[field]
                if old_docente_id and old_docente_id > 0:
                    new_docente_id = docente_map.get(old_docente_id)
                    if new_docente_id:
                        data_for_copy.append(( 
                            new_tramite_id, new_docente_id, i + 1, 5, system_user_id,
                            None, fecha_asignacion, 1
                        ))
                    else:
                        unmapped_jurados += 1
        
        print(f"  Se prepararon {len(data_for_copy)} registros para la carga masiva.")
        if unmapped_jurados > 0:
            print(f"  ADVERTENCIA: Se ignoraron {unmapped_jurados} jurados sin mapeo de ID.")

        # PASO 4: Cargar los datos en PostgreSQL usando COPY
        if data_for_copy:
            print("  Paso 4: Cargando datos en PostgreSQL con COPY...")
            buffer = io.StringIO()
            for record in data_for_copy:
                # CORRECCIÓN DEFINITIVA DEL ERROR UNICODEESCAPE
                line = '\t'.join(str(item) if item is not None else '\\N' for item in record)
                buffer.write(line + '\n')
            
            buffer.seek(0)

            columns = (
                'id_tramite', 'id_docente', 'id_orden', 'id_etapa', 
                'id_usuario_asignador', 'id_asignacion', 'fecha_asignacion', 'estado_cj'
            )
            
            # CORRECCIÓN 2: Usar '\N' en el comando SQL
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_conformacion_jurados ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')",
                file=buffer
            )
            
            pg_conn.commit()
            print(f"  Carga masiva completada. Se insertaron {len(data_for_copy)} registros.")

        print("--- Migración de tbl_conformacion_jurado (Inicial) completada con éxito ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en migración de conformación de jurados: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas ---")

if __name__ == '__main__':
    migrate_tbl_conformacion_jurado_fast()