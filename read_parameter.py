from PyQt5.QtWidgets import QMessageBox

def load_db_config():
    try:
        with open("db_config.txt", "r") as f:
            data = f.read().split(',')
            config = {
                "host": data[0],
                "dbname": data[1],
                "user": data[2],
                "password": data[3],
                "port": data[4]
            }
            return config
    except FileNotFoundError:
        QMessageBox.critical(None, "Error", "No se encontró el archivo de configuración. Configura la base de datos primero.")
        return None
