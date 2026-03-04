import psycopg2
from config import app_config

db_config = app_config.get_database_config()

conn = psycopg2.connect(
    host=db_config['host'],
    port=db_config['port'],
    dbname=db_config['db_name'],
    user=db_config['username'],
    password=db_config['password']
)

cur = conn.cursor()