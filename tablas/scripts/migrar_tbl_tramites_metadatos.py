import io
import os
import sys
import pandas as pd
import psycopg2

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_tramites_metadatos():
    """
    Migra todos los metadatos de trámites desde tesTramDoc (MySQL) a tbl_tramites_metadatos (PostgreSQL).
    
    La lógica es la siguiente:
    1. Se migran TODOS los registros de tesTramDoc.
    2. La 'id_etapa' se mapea siempre según el campo 'Tipo' (1->7, 2->12, 3->15).
    3. Se intenta buscar una 'fecha' correspondiente en tbl_dictamenes_info.
    4. Si no se encuentra una fecha, se utiliza la fecha y hora actual como fallback.
    """
    mysql_conn = get_mysql_pilar3_connection()
    postgres_conn = get_postgres_connection()

    if not all([mysql_conn, postgres_conn]):
        print("Error: No se pudieron establecer las conexiones a la base de datos.")
        return

    try:
        print("--- Iniciando migración de metadatos de trámites (lógica mejorada) ---")

        # 1. Obtener mapeos de IDs y datos de dictámenes desde PostgreSQL
        print("  Paso 1: Obteniendo mapeos y datos base desde PostgreSQL...")
        df_tramites_map = pd.read_sql("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL", postgres_conn)
        tramites_map = df_tramites_map.set_index('id_antiguo')['id'].to_dict()

        df_dictamenes = pd.read_sql("SELECT id, id_tramite, tipo_acta, fecha_dictamen, fecha_sustentacion FROM tbl_dictamenes_info", postgres_conn)
        df_dictamenes.sort_values('id', ascending=False, inplace=True)
        df_dictamenes.drop_duplicates(subset=['id_tramite', 'tipo_acta'], keep='first', inplace=True)
        dictamenes_map = df_dictamenes.set_index(['id_tramite', 'tipo_acta']).to_dict('index')
        print("  Mapeos y datos base obtenidos correctamente.")

        # 2. Extraer datos de metadatos desde MySQL
        print("  Paso 2: Extrayendo datos de tesTramDoc desde MySQL...")
        df_mysql = pd.read_sql(
            "SELECT IdTramite, Tipo, Title, Abstract, Keywords, Conclus FROM tesTramDoc",
            mysql_conn
        )
        print(f"  Se extrajeron {len(df_mysql)} registros de metadatos desde MySQL.")

        # 3. Transformar datos y aplicar la lógica de negocio
        print("  Paso 3: Transformando datos y aplicando lógica...")
        metadatos_list = []
        omitted_tramite_map = 0
        
        etapa_map = {1: 7, 2: 12, 3: 15}

        for _, row in df_mysql.iterrows():
            id_tramite_antiguo = row['IdTramite']
            tipo_doc = row['Tipo']
            
            id_tramite_nuevo = tramites_map.get(id_tramite_antiguo)
            if not id_tramite_nuevo:
                omitted_tramite_map += 1
                continue

            # Asignar la etapa siempre, basado en el Tipo
            id_etapa = etapa_map.get(tipo_doc)
            if not id_etapa:
                continue # Si el tipo no es 1, 2 o 3, se omite

            # Intentar encontrar la fecha; si no, usar fecha actual
            fecha = pd.Timestamp.now() # Valor por defecto
            dictamen_info = dictamenes_map.get((id_tramite_nuevo, tipo_doc))
            if dictamen_info:
                fecha_encontrada = None
                if tipo_doc in [1, 2]:
                    fecha_encontrada = dictamen_info.get('fecha_dictamen')
                elif tipo_doc == 3:
                    fecha_encontrada = dictamen_info.get('fecha_sustentacion')
                
                if pd.notna(fecha_encontrada):
                    fecha = fecha_encontrada

            metadatos_list.append({
                'id_tramite': id_tramite_nuevo,
                'titulo': row['Title'],
                'abstract': row['Abstract'],
                'keywords': row['Keywords'],
                'conclusiones': row['Conclus'],
                'presupuesto': 0,
                'id_etapa': id_etapa,
                'fecha': fecha,
                'estado_tm': 1
            })

        print(f"  Transformación completada. Se generaron {len(metadatos_list)} registros para insertar.")
        if omitted_tramite_map > 0:
            print(f"  Advertencia: {omitted_tramite_map} registros omitidos por no encontrar mapeo de trámite.")

        if not metadatos_list:
            print("No hay datos de metadatos para migrar.")
            return

        # 4. Cargar datos en PostgreSQL en lotes
        df_final = pd.DataFrame(metadatos_list)
        
        print("  Paso 4: Iniciando carga de datos a tbl_tramites_metadatos...")
        
        with postgres_conn.cursor() as cursor:
            # Limpiar la tabla antes de insertar para evitar duplicados en re-ejecuciones
            print("    Limpiando la tabla tbl_tramites_metadatos...")
            cursor.execute("TRUNCATE TABLE public.tbl_tramites_metadatos RESTART IDENTITY CASCADE;")

            # Procesar en lotes
            batch_size = 10000
            total_rows = len(df_final)
            
            print(f"    Cargando {total_rows} registros en lotes de {batch_size}...")
            
            for i in range(0, total_rows, batch_size):
                batch_df = df_final.iloc[i:i + batch_size]
                
                buffer = io.StringIO()
                batch_df.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
                buffer.seek(0)

                try:
                    cursor.copy_expert(
                        sql=r"""
                            COPY public.tbl_tramites_metadatos (
                                id_tramite, titulo, abstract, keywords, conclusiones,
                                presupuesto, id_etapa, fecha, estado_tm
                            ) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
                        """,
                        file=buffer
                    )
                    print(f"      - Lote {i // batch_size + 1}/{(total_rows // batch_size) + 1} cargado exitosamente.")
                except (Exception, psycopg2.Error) as batch_error:
                    print(f"      - ERROR en el lote {i // batch_size + 1}: {batch_error}")
                    postgres_conn.rollback() # Revertir el lote fallido
                    # Opcional: decidir si continuar con el siguiente lote o detener todo
                    continue 

        postgres_conn.commit()
        print(f"  Carga masiva completada. Se han migrado {len(df_final)} registros.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error durante la migración de metadatos de trámites: {error}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("--- Migración de metadatos de trámites finalizada. ---")

if __name__ == "__main__":
    migrate_tbl_tramites_metadatos()
