import psycopg2
from PyQt5.QtWidgets import QApplication, QMessageBox
from read_parameter import load_db_config

def connect_db():
    config = load_db_config()
    if config:
        try:
            conn = psycopg2.connect(
                dbname=config["dbname"],
                user=config["user"],
                password=config["password"],
                host=config["host"],
                port=config["port"]
            )
            return conn
        except Exception as e:
            # Usa QApplication.instance() para asegurar que la aplicación está inicializada
            if QApplication.instance():
                QMessageBox.critical(None, "Error", f"No se pudo conectar a la base de datos: {e}")
            else:
                print(f"No se pudo conectar a la base de datos: {e}")
            return None
    
def create_table():
    conn = connect_db()
    if conn:  # Verifica si la conexión es exitosa
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articulos (
                id SERIAL PRIMARY KEY,
                sales_person VARCHAR(100),
                net_sales DECIMAL,
                commission DECIMAL,
                item_description TEXT,
                store_name VARCHAR(50),
                item_number VARCHAR(50),
                date DATE, 
                comisionable BOOLEAN DEFAULT FALSE
            );
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    else:
        print("Error: No se pudo conectar a la base de datos para crear la tabla.")

