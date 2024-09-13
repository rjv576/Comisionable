import psycopg2

def connect_db():
    conn = psycopg2.connect(
        dbname="Comisionable",
        user="mi_usuario",
        password="Eridicald@12",
        host="localhost",
        port="5432"
    )
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articulos (
            id SERIAL PRIMARY KEY,
            item_description TEXT,
            item_number VARCHAR(50),
            comisionable BOOLEAN DEFAULT FALSE
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

create_table()
