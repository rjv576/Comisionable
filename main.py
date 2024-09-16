import init
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QCheckBox, QDateEdit
import sys



class ArticulosApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Artículos")
        self.resize(800, 600)

        # Crear una tabla
        self.table = QtWidgets.QTableWidget(self)
        self.table.setRowCount(0)  # Inicialmente no hay filas
        self.table.setColumnCount(4)  # Solo "Item Description", "Item Number", "Comisionable"
        self.table.setHorizontalHeaderLabels([
            "Store Name","Item Description", "Item Number", "Comisionable"
        ])

        # Crear widgets para las fechas
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QtCore.QDate.currentDate())  # Fecha de inicio predeterminada: hoy

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QtCore.QDate.currentDate())  # Fecha de fin predeterminada: hoy

        # Crear botones
        self.load_items_button = QtWidgets.QPushButton("Cargar Items de la DB")
        self.load_items_button.clicked.connect(self.load_items_from_db)

        self.import_button = QtWidgets.QPushButton("Importar Excel")
        self.import_button.clicked.connect(self.open_file_dialog)

        self.save_button = QtWidgets.QPushButton("Guardar Comisionables")
        self.save_button.clicked.connect(self.update_comisionable_in_db)

        self.export_button = QtWidgets.QPushButton("Calcular y Exportar Ganancias")
        self.export_button.clicked.connect(self.export_salesperson_earnings)

        # Crear layout
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(QtWidgets.QLabel("Fecha de inicio:"))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QtWidgets.QLabel("Fecha de fin:"))
        date_layout.addWidget(self.end_date_edit)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(date_layout)
        layout.addWidget(self.load_items_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.df = pd.DataFrame()  # DataFrame para almacenar los datos importados

    def open_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleccionar archivo Excel", "", "Excel Files (*.xls *.xlsx);;All Files (*)", options=options)
        if file_path:
            self.import_xls_to_db(file_path)

    def load_items_from_db(self):
        try:
            conn = init.connect_db()
            cursor = conn.cursor()

            # Convertir las fechas a string en formato 'YYYY-MM-DD'
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

            # Traer solo Item Description y Item Number sin duplicados, filtrados por rango de fechas
            cursor.execute('''
                SELECT DISTINCT store_name, item_description, item_number, comisionable
                FROM articulos
                WHERE date BETWEEN %s AND %s
            ''', (start_date, end_date))
            rows = cursor.fetchall()

            # Configurar la tabla
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    if j == 3:  # Columna "Comisionable"
                        checkbox = QCheckBox()
                        checkbox.setChecked(value == 'TRUE')
                        self.table.setCellWidget(i, j, checkbox)
                    else:
                        self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

            cursor.close()
            conn.close()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
            print(f"Error al cargar datos: {e}")

    def update_comisionable_in_db(self):
        try:
            conn = init.connect_db()
            cursor = conn.cursor()

            # Actualizar los valores de "comisionable" en la base de datos
            for row in range(self.table.rowCount()):
                item_description = self.table.item(row, 1).text() # Columna "Item Description"``
                item_number = self.table.item(row, 2).text() # Columna "Item Number"

                comisionable_widget = self.table.cellWidget(row, 3)  # Columna "Comisionable"
                comisionable_value = comisionable_widget.isChecked() if comisionable_widget else False

                cursor.execute('''
                    UPDATE articulos
                    SET comisionable = %s
                    WHERE item_description = %s AND item_number = %s
                ''', ('TRUE' if comisionable_value else 'FALSE', item_description, item_number))

            conn.commit()
            cursor.close()
            conn.close()
            QtWidgets.QMessageBox.information(self, "Éxito", "Cambios guardados exitosamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al guardar cambios: {e}")
            print(f"Error al guardar cambios: {e}")

    def import_xls_to_db(self, file_path):
        try:
            # Establecer la conexión
            conn = init.connect_db()
            cursor = conn.cursor()

            # Leer el archivo Excel
            self.df = pd.read_excel(file_path)

            # Normalizar nombres de las columnas (quitar espacios y convertir a minúsculas)
            normalized_columns = {col.strip().lower(): col for col in self.df.columns}

            # Ajustar los nombres exactos de las columnas
            def find_column(partial_name, columns):
                for col in columns:
                    if partial_name in col:
                        return columns[col]
                return None

            # Ajustar los nombres de acuerdo a lo visto en la imagen
            sales_person_col = find_column('salesperson name', normalized_columns)
            item_number_col = find_column('item number', normalized_columns)
            item_description_col = find_column('item description', normalized_columns)
            net_sales_col = find_column('net sales', normalized_columns)
            commission_col = find_column('commision', normalized_columns)
            store_name_col = find_column('store short name', normalized_columns)

            # Verificar que se encontraron todas las columnas necesarias
            if not item_number_col or not item_description_col or not net_sales_col or not commission_col or not sales_person_col:
                QtWidgets.QMessageBox.critical(self, "Error", "No se encontraron las columnas necesarias.")
                return

            # Iterar sobre las filas del DataFrame
            for index, row in self.df.iterrows():
                sales_person = row.get(sales_person_col, "")
                item_number = row.get(item_number_col, "")
                item_description = row.get(item_description_col, "")
                net_sales = row.get(net_sales_col, 0)
                commission = row.get(commission_col, 0)
                store_name = row.get(store_name_col, "")
                try:
                    # Insertar los datos en la base de datos, marcando comisionable como false por defecto
                    cursor.execute(
                            "INSERT INTO articulos (sales_person,net_sales,commission, item_description, store_name, item_number,comisionable) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (sales_person,net_sales,commission,item_description,store_name,item_number, False)  # Comisionable en False por defecto
                        )

                    # Hacer commit después de insertar todas las filas
                    conn.commit()
                    print("Datos importados exitosamente.")
                except Exception as e:
                    print(f"Error al importar los datos: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al importar datos: {e}")
            print(f"Error al importar datos: {e}")

        finally:
            # Cerrar la conexión de forma segura
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def export_salesperson_earnings(self):
        try:
            conn = init.connect_db()
            cursor = conn.cursor()

            # Convertir las fechas a string en formato 'YYYY-MM-DD'
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

            # Consultar articulos comisionables por cada salesperson en el rango de fechas
            cursor.execute('''
                SELECT store_name, sales_person, 
                           SUM(net_sales * 0.01) as revenue,
                           SUM(net_sales) as total_sale
                FROM articulos 
                WHERE comisionable = 'TRUE'
                AND date BETWEEN %s AND %s
                GROUP BY store_name, sales_person 
            ''', (start_date, end_date))

            rows = cursor.fetchall()
            df_earnings = pd.DataFrame(rows, columns=['Store Name','Sales Person', 'Revenue', 'Total Sale']) # Crear un DataFrame con los resultados

            # Exportar las ganancias a un archivo Excel
            options = QtWidgets.QFileDialog.Options()  # Opciones para el diálogo de guardar archivo
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar archivo Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
            if file_path:
                df_earnings.to_excel(file_path, index=False) # Exportar el DataFrame a un archivo Excel

                QtWidgets.QMessageBox.information(self, "Éxito", "Ganancias exportadas exitosamente.")
            
            cursor.close()
            conn.close()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al calcular o exportar ganancias: {e}")
            print(f"Error al calcular o exportar ganancias: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ArticulosApp()
    window.show()
    sys.exit(app.exec_())
