import sys
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QCheckBox, QDateEdit
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
import init
from read_parameter import load_db_config
from get_conection import ConfigDBDialog

print("Inicio del programa")

class ArticulosApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Artículos")
        self.resize(800, 600)

        # Crear una tabla
        self.table = QtWidgets.QTableWidget(self)
        self.table.setRowCount(0)  # Inicialmente no hay filas
        self.table.setColumnCount(3)  # Solo "Item Description", "Item Number", "Comisionable"
        self.table.setHorizontalHeaderLabels([
            "Item Description", "Item Number", "Comisionable"
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
        # Crear un botón para ordenar los items
        # Agregar un ComboBox para seleccionar el orden de clasificación
        self.sort_order_combo = QtWidgets.QComboBox(self)
        self.sort_order_combo.addItems(["A-Z", "Z-A"])
        self.sort_order_combo.currentIndexChanged.connect(self.load_items_from_db)

        # Crear layout
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addSpacerItem(QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)) # Espaciador
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

            order = "ASC" if self.sort_order_combo.currentText() == "A-Z" else "DESC"

            # Traer solo Item Description y Item Number sin duplicados, filtrados por rango de fechas
            cursor.execute('''
                SELECT DISTINCT  item_description, item_number, comisionable
                FROM articulos
                WHERE date BETWEEN %s AND %s
                ORDER BY item_description {}
            '''.format(order), (start_date, end_date))
            rows = cursor.fetchall()

            # Configurar la tabla
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    if j == 2:  # Columna "Comisionable"
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
                item_description = self.table.item(row, 0).text() # Columna "Item Description"``
                item_number = self.table.item(row, 1).text() # Columna "Item Number"

                comisionable_widget = self.table.cellWidget(row, 2)  # Columna "Comisionable"
                comisionable_value = comisionable_widget.isChecked() if comisionable_widget else False

                cursor.execute('''
                    UPDATE articulos
                    SET comisionable = %s
                    WHERE item_description = %s AND item_number = %s
                ''', ('FALSE' if comisionable_value else 'TRUE', item_description, item_number))

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
            date_col = find_column('date', normalized_columns)
            sales_person_col = find_column('salesperson name', normalized_columns)
            employee_id_col = find_column('employee id', normalized_columns) # Numero de empleado
            item_number_col = find_column('item number', normalized_columns)
            item_description_col = find_column('item description', normalized_columns)
            net_sales_col = find_column('net sales', normalized_columns)
            commission_col = find_column('commision', normalized_columns)
            store_name_col = find_column('store short name', normalized_columns)

            # Verificar que se encontraron todas las columnas necesarias
            if not item_number_col or not item_description_col or not net_sales_col or not commission_col or not sales_person_col or not store_name_col or not date_col or not employee_id_col:
                QtWidgets.QMessageBox.critical(self, "Error", "No se encontraron las columnas necesarias.")
                return

            # Iterar sobre las filas del DataFrame
            for index, row in self.df.iterrows():
                employee_id = row.get(employee_id_col, "") # Numero de empleado
                sales_person = row.get(sales_person_col, "")
                item_number = row.get(item_number_col, "")
                item_description = row.get(item_description_col, "")
                net_sales = row.get(net_sales_col, 0)
                commission = row.get(commission_col, 0)
                store_name = row.get(store_name_col, "")
                date = row.get(date_col, "")
                # Convertir la fecha a formato 'YYYY-MM-DD'
                if pd.notna(date):
                    date = pd.to_datetime(date).strftime('%Y-%m-%d')

                try:
                    # Insertar los datos en la base de datos, marcando comisionable como false por defecto
                    cursor.execute(
                            "INSERT INTO articulos (employee_id,sales_person,net_sales,commission, item_description, store_name, item_number, date , comisionable) "
                            "VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)",
                            (employee_id,sales_person,net_sales,commission,item_description,store_name,item_number,date, True)  # Comisionable en True por defecto
                        )

                    # Hacer commit después de insertar todas las filas
                    conn.commit()
                    print("Datos importados exitosamente.")
            
                except Exception as e:
                    print(f"Error al importar los datos: {e}")
                    
            QtWidgets.QMessageBox.information(self, "Éxito", "Datos importados exitosamente.")
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
            conn = init.connect_db()  # Conectar a la base de datos
            cursor = conn.cursor()

            # Convertir las fechas a string en formato 'YYYY-MM-DD'
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

            # Consultar artículos comisionables por cada salesperson en el rango de fechas
            cursor.execute('''
                SELECT employee_id, store_name, sales_person, 
                        SUM(net_sales * 0.01) as commission,
                        SUM(net_sales) as total_sale
                FROM articulos 
                WHERE comisionable = 'TRUE'
                AND date BETWEEN %s AND %s
                AND net_sales >= 0
                GROUP BY employee_id, store_name, sales_person 
            ''', (start_date, end_date))

            rows = cursor.fetchall()
            df_earnings = pd.DataFrame(rows, columns=['Employee ID', 'Store Name', 'Sales Person', 'Commission', 'Total Sale'])  # Crear un DataFrame con los resultados

            # Calcular los totales
            total_commission = round(df_earnings['Commission'].sum(), 2)
            total_sale = round(df_earnings['Total Sale'].sum(), 2)

            # Agregar la fila de "Gran Total"
            total_row = pd.DataFrame([['', '', 'Gran Total', total_commission, total_sale]], columns=df_earnings.columns)
            df_earnings = pd.concat([df_earnings, total_row], ignore_index=True)

            # Abrir un diálogo para guardar el archivo PDF
            file_dialog_options = QtWidgets.QFileDialog.Options()  # Opciones para el diálogo de guardar archivo
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar archivo PDF", "", "PDF Files (*.pdf);;All Files (*)", options=file_dialog_options)

            # Crear un documento PDF
            pdf = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []

            # Estilos para los párrafos
            styles = getSampleStyleSheet()

            # Encabezado del documento
            header_text = "Reporte de Ventas Comisionables"
            header = Paragraph(header_text, styles['Title'])

            # Agregar la fecha del reporte (fecha actual o rango de fechas del reporte)
            report_date_text = f"{datetime.now().strftime('%Y-%m-%d')}"
            report_date = Paragraph(report_date_text, styles['Normal'])

            # Convertir el DataFrame a una lista de listas (Filas y columnas con Paragraphs)
            data = [df_earnings.columns.tolist()]  # Agregar encabezados de columnas
            for index, row in df_earnings.iterrows():
                data.append([
                    Paragraph(str(row['Employee ID']), styles['BodyText']),
                    Paragraph(str(row['Store Name']), styles['BodyText']),
                    Paragraph(str(row['Sales Person']), styles['BodyText']),
                    f"{row['Commission']:,.2f}", # Formato de dos decimales
                    f"{row['Total Sale']:,.2f}" # Formato de dos decimales
                ])

            # Crear la tabla en reportlab con anchos de columna ajustables
            table = Table(data, colWidths=[1.5*inch]*5)  # 5 columnas con anchos iguales
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                # ('ALIGN', (0, 0), (-1, -1), 'CENTER'), Alinear todas las celdas al centro
                ('ALIGN', (3, 1), (4, -1), 'RIGHT'),    # Alinear "Commission" y "Total Sale" a la derecha
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (-1, -1), (-1, -1), colors.lightgrey),  # Fondo para la fila de "Gran Total"
                ('TEXTCOLOR', (-1, -1), (-1, -1), colors.black),  # Color de texto para la fila de "Gran Total"
                ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),  # Fuente para la fila de "Gran Total"
                ('FONTSIZE', (-1, -1), (-1, -1), 12),  # Tamaño de fuente para la fila de "Gran Total"
                # ('ALIGN', (-1, -1), (-1, -1), 'CENTER'),  # Alineación para la fila de "Gran Total"
            ])
            table.setStyle(table_style)
            elements.append(table)

            # Función para agregar encabezado con título y fechas
            def agregar_encabezado(canvas, doc, titulo, fecha_reporte, fecha_inicio, fecha_fin):
                canvas.saveState()
                canvas.setFont('Helvetica-Bold', 16)
                canvas.drawCentredString(4.25 * inch, 10.5 * inch, titulo)  # Título centrado en la parte superior
                canvas.setFont('Helvetica', 10)
                canvas.drawRightString(7.5 * inch, 10.25 * inch, f"Fecha del reporte: {fecha_reporte}")  # Fecha alineada a la derecha
                canvas.drawRightString(7.5 * inch, 10.0 * inch, f"Rango del reporte: {fecha_inicio} al {fecha_fin}")  # Rango de fechas
                canvas.restoreState()

            # Función para agregar número de páginas
            def agregar_numero_paginas(canvas, doc):
                canvas.saveState()
                page_num = canvas.getPageNumber()
                text = f"Página {page_num}"
                canvas.setFont('Helvetica', 10)
                canvas.drawCentredString(4.25 * inch, 0.75 * inch, text)  # Número de página en la parte inferior
                canvas.restoreState()

            # Crear el PDF con los elementos y la función de numeración de páginas
             # Crear el PDF con los elementos, título y la numeración de páginas
            pdf.build(elements, onFirstPage=lambda canvas, doc: agregar_encabezado(canvas, doc,  header_text,  report_date_text, start_date, end_date),
                    onLaterPages=lambda canvas, doc: [agregar_encabezado(canvas, doc,  header_text, report_date_text, start_date, end_date), agregar_numero_paginas(canvas, doc)])


            # Mostrar mensaje de éxito
            QtWidgets.QMessageBox.information(self, "Éxito", "Ganancias exportadas exitosamente.")
            
            

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al calcular o exportar ganancias: {e}")
            print(f"Error al calcular o exportar ganancias: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def main():
    # Crear la aplicación QApplication antes de crear cualquier ventana
    print("Inicializando QApplication")
    app = QtWidgets.QApplication(sys.argv)
    
    # Verificar si el archivo de configuración de la base de datos existe
    config = load_db_config()
    print(f"Configuración cargada: {config}")

    if not config:
        print("Mostrando diálogo de configuración de la DB")
        dialog = ConfigDBDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            init.create_table()  # Crear la tabla después de la configuración
    else:
        print("Creando tabla en la DB")
        # Si ya existe la configuración, crear la tabla y continuar
        init.create_table()

    # Crear la ventana principal después de la verificación
    window = ArticulosApp()
    window.show()

    # Ejecutar el ciclo de eventos de la aplicación
    print("Ejecutando la aplicación")
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()