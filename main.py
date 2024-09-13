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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "item_description", "item_number", "comisionable"
        ])

        # Crear botones
        self.import_button = QtWidgets.QPushButton("Importar Excel")
        self.import_button.clicked.connect(self.open_file_dialog)

        self.save_button = QtWidgets.QPushButton("Guardar Cambios")
        self.save_button.clicked.connect(self.update_comisionable_in_db)

        self.export_button = QtWidgets.QPushButton("Exportar a Excel")
        self.export_button.clicked.connect(self.export_to_xls)

        self.load_button = QtWidgets.QPushButton("Cargar Datos desde DB")
        self.load_button.clicked.connect(self.load_data_from_db)

        # Crear layout
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
        self.df = pd.read_excel(file_path)

        # Identificar las columnas 'item_number' y 'item_description' sin importar los nombres exactos
        columns_map = {col.lower(): col for col in self.df.columns}
        item_number_col = columns_map.get('item number')  # Buscar en minúsculas
        item_description_col = columns_map.get('item description')  # Buscar en minúsculas


        if not item_number_col or not item_description_col:
            QtWidgets.QMessageBox.critical(self, "Error", "No se encontraron las columnas 'Item Number' o 'Item_Description'")
            return

        # Detectar y eliminar duplicados antes de insertar en la base de datos
        self.df = self.df.drop_duplicates(subset=[item_number_col, item_description_col])

        for _, row in self.df.iterrows():
            # Verificar si el artículo ya existe en la base de datos
            if not self.is_duplicate_in_db(cursor, row[item_number_col], row[item_description_col]):
                cursor.execute('''
                    INSERT INTO articulos (item_description, item_number, comisionable)
                    VALUES (%s, %s, %s)
                ''', (
                    row[item_description_col],
                    row[item_number_col],
                    'TRUE' if row.get('comisionable', False) else 'FALSE'
                ))

        conn.commit()
        cursor.close()
        conn.close()
        QtWidgets.QMessageBox.information(self, "Éxito", "Datos importados exitosamente.")

    def is_duplicate_in_db(self, cursor, item_number, item_description):
        cursor.execute('''
            SELECT COUNT(*) FROM articulos
            WHERE item_number = %s AND item_description = %s
        ''', (item_number, item_description))
        return cursor.fetchone()[0] > 0

    def load_data_from_db(self):
        try:
            conn = init.connect_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articulos')
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    if j == 3:  # Columna "comisionable"
                        checkbox = QCheckBox()
                        checkbox.setChecked(value == 'FALSE')
                        checkbox.stateChanged.connect(lambda state, row=i: self.update_comisionable_value(row, state))
                        self.table.setCellWidget(i, j, checkbox)
                    else:
                        self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

            cursor.close()
            conn.close()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
            print(f"Error al cargar datos: {e}")

    def update_comisionable_value(self, row, state):
        self.df.at[row, 'comisionable'] = bool(state)

    def update_comisionable_in_db(self):
            try:
                conn = init.connect_db()
                cursor = conn.cursor()

                for row in range(self.table.rowCount()):
                    item_id = self.table.item(row, 0).text()  # Asumiendo que el 'ID' está en la primera columna
                    comisionable_widget = self.table.cellWidget(row, 3)  # El checkbox está en la cuarta columna
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

            data = []
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(columnCount)]

            for row in range(rowCount):
                rowData = []
                for column in range(columnCount):
                    if column == 3:  # Columna 'comisionable' con el checkbox
                        checkbox = self.table.cellWidget(row, column)
                        rowData.append(checkbox.isChecked())
                    else:
                        item = self.table.item(row, column)
                        rowData.append(item.text() if item else "")
                data.append(rowData)

            df = pd.DataFrame(data, columns=headers)

            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar archivo Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                QtWidgets.QMessageBox.information(self, "Éxito", "Datos exportados exitosamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al exportar datos: {e}")
            print(f"Error al exportar datos: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ArticulosApp()
    window.show()
    sys.exit(app.exec_())
