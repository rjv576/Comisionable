import init
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QCheckBox
import sys

class ArticulosApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Artículos")
        self.resize(800, 600)
        
        # Crear una tabla
        self.table = QtWidgets.QTableWidget(self)
        self.table.setRowCount(0)
        self.table.setColumnCount(19)
        self.table.setHorizontalHeaderLabels([
            "ID", "salesperson_name", "store_short_name", "net_sales", "order_number", "promocion_sales", 
            "item_description", "territory", "department_code", "department_name", "item_number", 
            "transation", "comision", "date", "fineline_code", "fineline_name", "class_code", 
            "class_name", "comisionable"
        ])

        # Crear botones y campos de entrada
        self.import_button = QtWidgets.QPushButton("Importar Excel")
        self.import_button.clicked.connect(self.open_file_dialog)
        
        self.save_button = QtWidgets.QPushButton("Guardar Cambios")
        self.save_button.clicked.connect(self.update_comisionable_in_db)
        
        self.export_button = QtWidgets.QPushButton("Exportar a Excel")
        self.export_button.clicked.connect(self.export_to_xls)

        self.load_button = QtWidgets.QPushButton("Cargar Datos desde DB")
        self.load_button.clicked.connect(self.load_data_from_db)

        # Crear layout y agregar widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.import_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.load_button)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.df = pd.DataFrame()  # DataFrame para almacenar los datos importados

    def open_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleccionar archivo Excel", "", "Excel Files (*.xls *.xlsx);;All Files (*)", options=options)
        if file_path:
            self.import_xls_to_db(file_path)

    def import_xls_to_db(self, file_path):
        conn = init.connect_db()
        cursor = conn.cursor()

        # Leer el archivo Excel
        self.df = pd.read_excel(file_path)  # Actualizamos self.df con los datos importados

        # Convertir la columna 'comisionable' al tipo booleano
        self.df['comisionable'] = self.df['comisionable'].astype(bool)

        # Verificar que todas las columnas necesarias están presentes
        required_columns = [
            'salesperson_name', 'store_short_name', 'net_sales', 'order_number', 'promocion_sales',
            'item_description', 'territory', 'department_code', 'department_name', 'item_number', 'transation',
            'comision', 'date', 'fineline_code', 'fineline_name', 'class_code', 'class_name', 'comisionable'
        ]
        for column in required_columns:
            if column not in self.df.columns:
                QtWidgets.QMessageBox.critical(self, "Error", f"Falta la columna requerida: {column}")
                return

        # Iterar sobre el DataFrame e insertar datos en la base de datos
        for _, row in self.df.iterrows():
            cursor.execute('''
                INSERT INTO articulos (
                    salesperson_name, store_short_name, net_sales, order_number, promocion_sales,
                    item_description, territory, department_code, department_name, item_number, 
                    transation, comision, date, fineline_code, fineline_name, class_code, 
                    class_name, comisionable
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                row['salesperson_name'], row['store_short_name'], row['net_sales'], row['order_number'], 
                row['promocion_sales'], row['item_description'], row['territory'], row['department_code'], 
                row['department_name'], row['item_number'], row['transation'], row['comision'], 
                row['date'], row['fineline_code'], row['fineline_name'], row['class_code'], 
                row['class_name'], 'TRUE' if row['comisionable'] else 'FALSE'
            ))

        conn.commit()
        cursor.close()
        conn.close()
        QtWidgets.QMessageBox.information(self, "Éxito", "Datos importados exitosamente.")

    def load_data_from_db(self):
        try:
            # Inicializar la conexión
            conn = init.connect_db()
            
            # Verificar la conexión antes de usar el cursor
            if conn is None:
                raise Exception("No se pudo conectar a la base de datos.")
            
            # Crear un cursor
            cursor = conn.cursor()

            # Ejecutar la consulta
            cursor.execute('SELECT * FROM articulos')
            rows = cursor.fetchall()

            # Verificar si se obtuvieron filas
            if not rows:
                raise Exception("No se encontraron datos en la tabla 'articulos'.")

            # Configurar la tabla solo si hay resultados
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(19)
            
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    if j == 18:  # Columna "comisionable"
                        checkbox = QCheckBox()
                        checkbox.setChecked(bool(value))  # Asegurarse de que sea booleano
                        checkbox.stateChanged.connect(lambda state, row=i: self.update_comisionable_value(row, state))
                        self.table.setCellWidget(i, j, checkbox)
                    else:
                        self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

            # Cerrar cursor y conexión
            cursor.close()
            conn.close()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
            print(f"Error al cargar datos: {e}")

    def update_comisionable_value(self, row, state):
        # Almacenar el valor actualizado del checkbox en el DataFrame
        self.df.at[row, 'comisionable'] = bool(state) 

    def update_comisionable_in_db(self):
        try:
            conn = init.connect_db()
            cursor = conn.cursor()

            # Iterar sobre las filas de la tabla y actualizar la columna 'comisionable'
            for row in range(self.table.rowCount()):
                item_id = self.table.item(row, 0).text()  # Suponiendo que el 'ID' está en la primera columna
                comisionable_widget = self.table.cellWidget(row, 18)  # El checkbox está en la columna 18
                comisionable_value = comisionable_widget.isChecked()

                cursor.execute('''
                    UPDATE articulos
                    SET comisionable = %s
                    WHERE id = %s
                ''', ('TRUE' if comisionable_value else 'FALSE', item_id))

            conn.commit()
            cursor.close()
            conn.close()
            QtWidgets.QMessageBox.information(self, "Éxito", "Cambios guardados exitosamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al guardar cambios: {e}")
            print(f"Error al guardar cambios: {e}")

    def export_to_xls(self):
        try:
            rowCount = self.table.rowCount()
            columnCount = self.table.columnCount()

            # Crear un DataFrame vacío
            data = []
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(columnCount)]

            # Rellenar el DataFrame con los datos de la tabla
            for row in range(rowCount):
                rowData = []
                for column in range(columnCount):
                    if column == 18:  # Columna 'comisionable' con el checkbox
                        checkbox = self.table.cellWidget(row, column)
                        rowData.append(checkbox.isChecked())
                    else:
                        item = self.table.item(row, column)
                        rowData.append(item.text() if item else "")
                data.append(rowData)

            df = pd.DataFrame(data, columns=headers)

            # Guardar el DataFrame en un archivo Excel
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar archivo Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                QtWidgets.QMessageBox.information(self, "Éxito", "Datos exportados exitosamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al exportar datos: {e}")
            print(f"Error al exportar datos: {e}")

# Ejecut
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ArticulosApp()
    window.show()
    sys.exit(app.exec_())