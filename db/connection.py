import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

def get_connection():
    """
    Crée et retourne une connexion à PostgreSQL.
    Les paramètres sont lus depuis le fichier .env
    """
    return psycopg.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        row_factory=dict_row
    )