# Este archivo contendrá la configuración y las funciones 
# para conectarse a las bases de datos de MySQL y PostgreSQL.

# Es posible que necesites instalar las librerías si no las tienes:
# pip install mysql-connector-python psycopg2-binary

import mysql.connector
import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de Conexiones ---

MYSQL_CONFIG_ABSMAIN = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'vriunap_absmain'
}

MYSQL_CONFIG_PILAR3 = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'vriunap_pilar3'
}

# --- Conexión a Supabase (Configuración Activa) ---
# La configuración ahora se toma de la variable de entorno DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")


# --- Funciones de Conexión ---

def get_mysql_absmain_connection():
    """Devuelve una conexión a la base de datos vriunap_absmain en MySQL."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG_ABSMAIN)
        print("Conexión exitosa a MySQL (vriunap_absmain).")
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a MySQL (vriunap_absmain): {err}")
        return None

def get_mysql_pilar3_connection():
    """Devuelve una conexión a la base de datos vriunap_pilar3 en MySQL."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG_PILAR3)
        print("Conexión exitosa a MySQL (vriunap_pilar3).")
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a MySQL (vriunap_pilar3): {err}")
        return None

def get_postgres_connection():
    """Devuelve una conexión a la base de datos de PostgreSQL local."""
    try:
        # --- Conexión a PostgreSQL Local ---
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="admin",
            password="admin123",
            dbname="postgres"
        )
        print("Conexión exitosa a PostgreSQL Local.")
        return conn
    except psycopg2.Error as err:
        print(f"Error al conectar a PostgreSQL Local: {err}")
        return None

# --- Conexión a Supabase (Desactivada) ---
# def get_postgres_connection():
#     """Devuelve una conexión a la base de datos de PostgreSQL usando DATABASE_URL."""
#     try:
#         if not DATABASE_URL:
#             raise ValueError("La variable de entorno DATABASE_URL no está definida.")
#         conn = psycopg2.connect(DATABASE_URL)
#         print("Conexión exitosa a PostgreSQL (Supabase).")
#         return conn
#     except (psycopg2.Error, ValueError) as err:
#         print(f"Error al conectar a PostgreSQL (Supabase): {err}")
#         return None




