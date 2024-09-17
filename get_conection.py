# Este file ofrece una interfaz para solicitar una conexión a la base de datos
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLineEdit, QLabel, QPushButton, QVBoxLayout, QMessageBox

class ConfigDBDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configurar Conexión a Base de Datos")

        # Campos para los parámetros de conexión
        self.host_edit = QLineEdit(self)
        self.dbname_edit = QLineEdit(self)
        self.user_edit = QLineEdit(self)
        self.password_edit = QLineEdit(self)
        self.port_edit = QLineEdit(self)
        
        # Añadir etiquetas y campos de entrada
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Host:"))
        layout.addWidget(self.host_edit)
        layout.addWidget(QLabel("Nombre de la Base de Datos:"))
        layout.addWidget(self.dbname_edit)
        layout.addWidget(QLabel("Usuario:"))
        layout.addWidget(self.user_edit)
        layout.addWidget(QLabel("Contraseña:"))
        layout.addWidget(self.password_edit)
        layout.addWidget(QLabel("Puerto:"))
        layout.addWidget(self.port_edit)

        # Botón de guardar
        self.save_button = QPushButton("Guardar Configuración")
        self.save_button.clicked.connect(self.save_db_config)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_db_config(self):
        # Recuperar los datos ingresados
        host = self.host_edit.text()
        dbname = self.dbname_edit.text()
        user = self.user_edit.text()
        password = self.password_edit.text()
        port = self.port_edit.text()
        
        # Validar los campos
        if not host or not dbname or not user or not password or not port:
            QMessageBox.critical(self, "Error", "Todos los campos son obligatorios.")
            return

        # Guardar la configuración en un archivo (o base de datos local)
        with open("db_config.txt", "w") as f:
            f.write(f"{host},{dbname},{user},{password},{port}")
        
        QMessageBox.information(self, "Éxito", "Configuración de la base de datos guardada correctamente.")
        self.accept()
