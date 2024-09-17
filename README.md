# Comisionable
La aplicación de gestión de artículos es una herramienta de escritorio diseñada para facilitar la administración y el análisis de datos de ventas. Permite a los usuarios importar datos desde archivos Excel, actualizar el estado de los artículos como "comisionables", y calcular las ganancias de los vendedores. La aplicación se conecta a una base de datos PostgreSQL para almacenar y gestionar los datos, proporcionando una interfaz gráfica intuitiva para realizar estas tareas.

Cómo Funciona

Configuración de la Base de Datos:

Al iniciar la aplicación, si no encuentra el archivo de configuración db_config.txt, solicita al usuario que cree uno. Este archivo debe contener los detalles necesarios para conectarse a la base de datos (host, nombre de la base de datos, usuario, contraseña y puerto).
Interfaz Principal:

Visualización de Datos: Muestra una tabla con los artículos importados que incluye detalles como descripción del artículo, número de artículo y si es comisionable.
Filtros de Fecha: Permite seleccionar un rango de fechas para filtrar los datos de ventas.
Botones de Acción:
Cargar Items: Trae los datos de los artículos desde la base de datos y los muestra en la tabla.
Importar Excel: Permite al usuario seleccionar un archivo Excel para importar datos de ventas y almacenarlos en la base de datos.
Guardar Comisionables: Actualiza el estado de los artículos como "comisionables" en la base de datos según las selecciones en la tabla.
Calcular y Exportar Ganancias: Calcula las ganancias de los vendedores en función de las ventas comisionables y exporta el resultado a un archivo Excel.
Operaciones con Datos:

Importación de Datos: Lee datos desde un archivo Excel, normaliza los nombres de las columnas, y guarda la información en la base de datos.
Actualización de Artículos: Permite marcar artículos como comisionables y guarda estos cambios en la base de datos.
Cálculo y Exportación: Realiza cálculos sobre las ventas comisionables y exporta un reporte de ganancias a un archivo Excel.
Distribución:

La aplicación se distribuye como un archivo ejecutable y debe incluir un archivo de ejemplo (db_config_example.txt) con instrucciones para crear el archivo de configuración necesario.
Esta aplicación facilita la gestión eficiente de los datos de ventas y proporciona una interfaz amigable para la actualización y análisis de la información.
