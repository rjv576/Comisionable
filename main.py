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
        self.table.setRowCount(0)  # Inicialmente no hay filas
        self.table.setColumnCount(8)  # Añadir una columna para el checkbox de "comisionable"
        self.table.setHorizontalHeaderLabels([
            "Id","Sales Person", "Net Sales", "Commision", "Item Description", "Item Number", "Time", "Comisionable"
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

            # Aquí puedes insertar los datos en la base de datos
            cursor.execute(
                "INSERT INTO articulos (sales_person, item_number, item_description, net_sales, commission) VALUES (%s, %s, %s, %s, %s)",
                (sales_person, item_number, item_description, net_sales, commission)
            )

        conn.commit()
        cursor.close()
        conn.close()
        
         # Mostrar mensaje de éxito
        QtWidgets.QMessageBox.information(self, "Éxito", "Los datos se han cargado exitosamente en la base de datos.")

    def load_data_from_db(self):
        try:
            conn = init.connect_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id,sales_person, net_sales, commission, item_description, item_number, date, comisionable FROM articulos')
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    if j == 7:  # Columna "comisionable"
                        checkbox = QCheckBox()
                        checkbox.setChecked(value == 'TRUE')
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

            # Actualizar los valores en la base de datos
            for row in range(self.table.rowCount()):
                item_id_item = self.table.item(row, 0)
                if item_id_item is not None:
                    item_id = item_id_item.text()
                else:
                    continue  # Saltar la fila si no tiene valor en la primera columna (ID)

                comisionable_widget = self.table.cellWidget(row, 7)  # Columna "comisionable"
                comisionable_value = comisionable_widget.isChecked() if comisionable_widget else False

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

            # Obtener encabezados de columnas
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(columnCount)]

            # Añadir las columnas "Comisionable" y "Ganancia"
            headers.append("Comisionable")
            headers.append("Ganancia")

            data = []
            salesperson_commissions = {}

            for row in range(rowCount):
                rowData = []
                comisionable_widget = self.table.cellWidget(row, 7)  # Índice 7 para "comisionable"
                comisionable_value = comisionable_widget.isChecked() if comisionable_widget else False

                net_sales = 0
                commission = 0
                salesperson = ""

                for column in range(columnCount):
                    item = self.table.item(row, column)
                    if item:
                        text = item.text()
                        rowData.append(text)

                        # Extraer valores de las columnas específicas
                        if column == 1:  # Columna "Salesperson" (índice 0)
                            salesperson = text
                        elif column == 2:  # Columna "Net Sales" (índice 2)
                            try:
                                net_sales = float(text)
                            except ValueError:
                                net_sales = 0
                        elif column == 3:  # Columna "Commision" (índice 3)
                            try:
                                commission = float(text)
                            except ValueError:
                                commission = 0
                    else:
                        rowData.append("")

                # Añadir el valor de "Comisionable" a rowData
                rowData.append(comisionable_value)

                # Calcular ganancia si es comisionable
                if comisionable_value:
                    ganancia = net_sales * commission  # Se calcula solo si es comisionable
                    rowData.append(ganancia)

                    # Acumular comisiones por salesperson si es comisionable
                    if salesperson in salesperson_commissions:
                        salesperson_commissions[salesperson] += ganancia
                    else:
                        salesperson_commissions[salesperson] = ganancia
                else:
                    rowData.append(0)  # Si no es comisionable, ganancia es 0

                data.append(rowData)

            # Crear el DataFrame con los datos y los encabezados
            df = pd.DataFrame(data, columns=headers)

            # Crear el DataFrame para el resumen de comisiones por salesperson
            summary_data = [{'Salesperson': salesperson, 'Total Ganancia': total_ganancia}
                            for salesperson, total_ganancia in salesperson_commissions.items()]
            df_summary = pd.DataFrame(summary_data)

            # Guardar el archivo Excel con ambas hojas
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar archivo Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
            if file_path:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # Guardar la tabla principal en la primera hoja
                    df.to_excel(writer, sheet_name='Datos', index=False)
                    # Guardar la tabla resumen en una segunda hoja
                    df_summary.to_excel(writer, sheet_name='Resumen de Comisiones', index=False)

                QtWidgets.QMessageBox.information(self, "Éxito", "Datos y resumen de comisiones exportados exitosamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al exportar datos: {e}")
            print(f"Error al exportar datos: {e}")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ArticulosApp()
    window.show()
    sys.exit(app.exec_())
