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
            salesperson_name VARCHAR(255),
            store_short_same VARCHAR(255),
            net_sales DECIMAL,
            order_number VARCHAR(50),
            promocion_sales DECIMAL,
            item_description TEXT,
            territory VARCHAR(255),
            department_code VARCHAR(50),
            department_name VARCHAR(255),
            item_number VARCHAR(50),
            transation VARCHAR(50),
            comision DECIMAL,
            date DATE,
            fineline_code VARCHAR(50),
            fineline_name VARCHAR(255),
            class_code VARCHAR(50),
            class_name VARCHAR(255),
            comisionable BOOLEAN DEFAULT FALSE
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

create_table()
