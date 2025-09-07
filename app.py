import requests
import os
import sys
from datetime import datetime

# Add the parent directory to the Python path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from podb_connections import get_postgres_connection

# --- Configuration ---
API_BASE_URL = "https://service7.unap.edu.pe/api/v1/sunedu/consulta/{dni}"
API_TOKEN = "1|xrpNWzmI8EdDfvnKQpURERHiO4RraB4WmcIr810MjapBmmjXKWNGczJGTY"

def populate_estudios_from_sunedu():
    """
    Fetches academic degrees from the SUNEDU API for each user in tbl_usuarios
    and populates the tbl_estudios and dic_universidades tables.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        print("✅ Connected to PostgreSQL.")

        # 1. Clean destination tables as requested
        print("🧹 Clearing tbl_estudios and dic_universidades for a fresh start...")
        cur.execute("TRUNCATE TABLE public.tbl_estudios RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE public.dic_universidades RESTART IDENTITY CASCADE;")
        print("   Tables cleared successfully.")

        # 2. Pre-load dictionaries from the database for efficiency
        cur.execute("SELECT abreviatura, id FROM dic_grados_academicos")
        grados_map = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("SELECT nombre, id FROM dic_obtencion_studios WHERE nombre = 'API SUNEDU'")
        api_obtencion_id = cur.fetchone()[1]
        
        print(f"📚 Pre-loaded {len(grados_map)} academic degrees and obtention type ID.")

        # 3. Fetch all users (DNI and ID) from tbl_usuarios
        cur.execute("SELECT id, num_doc_identidad FROM tbl_usuarios WHERE num_doc_identidad ~ '^[0-9]{8}$'")
        users = cur.fetchall()
        total_users = len(users)
        print(f"👥 Found {total_users} users with valid DNIs to process.")

        university_cache = {} # Cache to avoid redundant DB queries for universities

        # 4. Iterate over each user, query the API, and populate the database
        for i, (user_id, dni) in enumerate(users):
            print(f"\n--- Processing user {i+1}/{total_users} (DNI: {dni}) ---")
            
            try:
                headers = {'Authorization': f'Bearer {API_TOKEN}'}
                response = requests.get(API_BASE_URL.format(dni=dni), headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"   ❌ API Error: Received status code {response.status_code}")
                    continue

                data = response.json().get('data', {}).get('gtPersona', [])
                if not data:
                    print("   ℹ️ No academic degrees found for this DNI.")
                    continue
                
                print(f"   ✅ Found {len(data)} academic degree(s).")

                for degree in data:
                    # 5. Find or Create University
                    uni_name = degree.get('universidad')
                    if not uni_name:
                        continue

                    if uni_name in university_cache:
                        uni_id = university_cache[uni_name]
                    else:
                        cur.execute("SELECT id FROM dic_universidades WHERE nombre = %s", (uni_name,))
                        result = cur.fetchone()
                        if result:
                            uni_id = result[0]
                        else:
                            print(f"      -> New University: '{uni_name}'. Adding to dictionary.")
                            cur.execute(
                                """
                                INSERT INTO dic_universidades (nombre, pais, tipo_institucion, tipo_gestion, estado_dic_universidades)
                                VALUES (%s, %s, %s, %s, %s) RETURNING id;
                                """,
                                (
                                    uni_name,
                                    degree.get('pais'),
                                    degree.get('tipoInstitucion'),
                                    degree.get('tipoGestion'),
                                    True
                                )
                            )
                            uni_id = cur.fetchone()[0]
                        university_cache[uni_name] = uni_id

                    # 6. Map data and insert into tbl_estudios
                    grado_abbr = degree.get('abreviaturaTitulo')
                    if grado_abbr not in grados_map:
                        print(f"      ⚠️ Skipping degree: Unknown abbreviation '{grado_abbr}'")
                        continue
                    
                    # Format date from DD/MM/YYYY to YYYY-MM-DD
                    try:
                        fecha_emision = datetime.strptime(degree.get('fechaEmision'), '%d/%m/%Y').strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        fecha_emision = None

                    cur.execute(
                        """
                        INSERT INTO tbl_estudios (
                            id_usuario, id_universidad, id_grado_academico, titulo_profesional,
                            especialidad, fecha_emision, resolucion, id_tipo_obtencion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (
                            user_id,
                            uni_id,
                            grados_map[grado_abbr],
                            degree.get('tituloProfesional'),
                            degree.get('especialidad'),
                            fecha_emision,
                            degree.get('resolucion'),
                            api_obtencion_id
                        )
                    )
                    print(f"      -> Inserted: {degree.get('tituloProfesional')}")

                conn.commit()

            except requests.exceptions.RequestException as e:
                print(f"   ❌ Network Error: {e}")
            except Exception as e:
                print(f"   ❌ An unexpected error occurred: {e}")
                conn.rollback()

        print("\n🎉 Process completed successfully!")

    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("PostgreSQL connection closed.")

if __name__ == "__main__":
    populate_estudios_from_sunedu()