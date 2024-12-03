import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import date


# Leer datos de categorías y usuarios desde un archivo JSON
def cargar_datos_json():
    try:
        with open("data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        st.warning("El archivo data.json no se encontró. Asegúrate de que exista.")
        return {"categorias": [], "usuarios": []}


# Guardar los datos de categorías y usuarios en el archivo JSON
def guardar_datos_json(datos):
    with open("data.json", "w") as file:
        json.dump(datos, file, indent=4)


# Crear conexión con SQLite
conn = sqlite3.connect("finanzas.db")
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_categoria TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('Ingreso', 'Gasto'))
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS subcategorias (
    id_subcategoria INTEGER PRIMARY KEY AUTOINCREMENT,
    id_categoria INTEGER NOT NULL,
    nombre_subcategoria TEXT NOT NULL,
    FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria)
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS transacciones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('Ingreso', 'Gasto')),
    monto REAL NOT NULL,
    id_subcategoria INTEGER NOT NULL,
    descripcion TEXT,
    id_usuario INTEGER NOT NULL,
    FOREIGN KEY (id_subcategoria) REFERENCES subcategorias (id_subcategoria),
    FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
)
"""
)
conn.commit()


# Funciones para manejar la base de datos
def importar_datos_json(datos):
    """Importar los datos de data.json a la base de datos SQLite"""
    # Insertar categorías
    for categoria in datos.get("categorias", []):
        cursor.execute(
            """
            INSERT OR IGNORE INTO categorias (id_categoria, nombre_categoria, tipo)
            VALUES (?, ?, ?)
            """,
            (
                categoria["id_categoria"],
                categoria["nombre_categoria"],
                categoria["tipo"],
            ),
        )
        # Insertar subcategorías relacionadas
        for subcategoria in categoria.get("subcategorias", []):
            cursor.execute(
                """
                INSERT OR IGNORE INTO subcategorias (id_subcategoria, id_categoria, nombre_subcategoria)
                VALUES (?, ?, ?)
                """,
                (
                    subcategoria["id_subcategoria"],
                    categoria["id_categoria"],
                    subcategoria["nombre_subcategoria"],
                ),
            )

    # Insertar usuarios
    for usuario in datos.get("usuarios", []):
        cursor.execute(
            """
            INSERT OR IGNORE INTO usuarios (id_usuario, nombre)
            VALUES (?, ?)
            """,
            (usuario["id_usuario"], usuario["nombre"]),
        )

    conn.commit()


def agregar_usuario(nombre):
    cursor.execute(
        "INSERT INTO usuarios (nombre) VALUES (?)",
        (nombre,),
    )
    conn.commit()


def obtener_usuarios():
    cursor.execute("SELECT id_usuario, nombre FROM usuarios")
    return cursor.fetchall()


def agregar_categoria(nombre_categoria, tipo):
    cursor.execute(
        "INSERT INTO categorias (nombre_categoria, tipo) VALUES (?, ?)",
        (nombre_categoria, tipo),
    )
    conn.commit()


def obtener_categorias(tipo=None):
    if tipo:
        cursor.execute(
            "SELECT id_categoria, nombre_categoria FROM categorias WHERE tipo = ?",
            (tipo,),
        )
    else:
        cursor.execute("SELECT id_categoria, nombre_categoria FROM categorias")
    return cursor.fetchall()


def agregar_subcategoria(id_categoria, nombre_subcategoria):
    cursor.execute(
        "INSERT INTO subcategorias (id_categoria, nombre_subcategoria) VALUES (?, ?)",
        (id_categoria, nombre_subcategoria),
    )
    conn.commit()


def obtener_subcategorias(id_categoria=None):
    if id_categoria:
        cursor.execute(
            "SELECT id_subcategoria, nombre_subcategoria FROM subcategorias WHERE id_categoria = ?",
            (id_categoria,),
        )
    else:
        cursor.execute("SELECT id_subcategoria, nombre_subcategoria FROM subcategorias")
    return cursor.fetchall()


def agregar_transaccion(fecha, tipo, monto, id_subcategoria, descripcion, id_usuario):
    cursor.execute(
        "INSERT INTO transacciones (fecha, tipo, monto, id_subcategoria, descripcion, id_usuario) VALUES (?, ?, ?, ?, ?, ?)",
        (fecha, tipo, monto, id_subcategoria, descripcion, id_usuario),
    )
    conn.commit()


def obtener_transacciones():
    query = """
    SELECT t.fecha, t.tipo, t.monto, c.nombre_categoria, s.nombre_subcategoria, t.descripcion, u.nombre 
    FROM transacciones t 
    JOIN subcategorias s ON t.id_subcategoria = s.id_subcategoria
    JOIN categorias c ON s.id_categoria = c.id_categoria
    JOIN usuarios u ON t.id_usuario = u.id_usuario
    ORDER BY t.fecha DESC
    """
    return pd.read_sql_query(query, conn)


# Interfaz de Streamlit
st.title("Registro de Ingresos y Gastos")
st.sidebar.header("Opciones")

opcion = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "Registrar",
        "Ver Transacciones",
        "Agregar Categorías",
        "Agregar Subcategorías",
        "Agregar Usuarios",
        "Importar Datos desde JSON",
    ],
)

# Cargar datos JSON
datos_json = cargar_datos_json()

if opcion == "Importar Datos desde JSON":
    st.header("Importar Datos desde JSON")
    if st.button("Importar"):
        importar_datos_json(datos_json)
        st.success("Datos importados correctamente desde data.json.")


if opcion == "Registrar":
    st.header("Registrar Ingreso o Gasto")
    col1, col2 = st.columns(2)

    with col1:
        tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        monto = st.number_input("Monto", min_value=0.0, format="%.2f")
        fecha = st.date_input("Fecha", value=date.today())

    with col2:
        categorias = obtener_categorias(tipo)
        if not categorias:
            st.warning(
                f"No hay categorías para {tipo}. Por favor, agrega una categoría."
            )
        else:
            categoria = st.selectbox(
                "Categoría",
                options=[(c[0], c[1]) for c in categorias],
                format_func=lambda x: x[1],
            )
            subcategorias = obtener_subcategorias(categoria[0])
            if not subcategorias:
                st.warning("No hay subcategorías para esta categoría.")
            else:
                subcategoria = st.selectbox(
                    "Subcategoría",
                    options=[(s[0], s[1]) for s in subcategorias],
                    format_func=lambda x: x[1],
                )
                descripcion = st.text_area("Descripción (opcional)")
                usuarios = obtener_usuarios()
                usuario = st.selectbox(
                    "Usuario",
                    options=[(u[0], u[1]) for u in usuarios],
                    format_func=lambda x: x[1],
                )

    if st.button("Guardar"):
        if categoria and subcategoria:
            agregar_transaccion(
                fecha, tipo, monto, subcategoria[0], descripcion, usuario[0]
            )
            st.success("Transacción registrada correctamente.")
        else:
            st.error("Debe seleccionar una categoría y subcategoría.")

elif opcion == "Ver Transacciones":
    st.header("Ver Transacciones Registradas")
    transacciones = obtener_transacciones()
    st.dataframe(transacciones)

elif opcion == "Agregar Categorías":
    st.header("Agregar Nueva Categoría")
    tipo_categoria = st.selectbox("Tipo de Categoría", ["Ingreso", "Gasto"])
    nombre_categoria = st.text_input("Nombre de la Categoría")

    if st.button("Agregar Categoría"):
        if nombre_categoria:
            agregar_categoria(nombre_categoria, tipo_categoria)
            datos_json["categorias"].append(
                {
                    "id_categoria": len(datos_json["categorias"]) + 1,
                    "nombre_categoria": nombre_categoria,
                    "tipo": tipo_categoria,
                    "subcategorias": [],
                }
            )
            guardar_datos_json(datos_json)
            st.success("Categoría agregada correctamente.")
        else:
            st.error("Debe ingresar un nombre para la categoría.")

elif opcion == "Agregar Subcategorías":
    st.header("Agregar Nueva Subcategoría")
    categorias = obtener_categorias()
    categoria_seleccionada = st.selectbox(
        "Selecciona Categoría",
        options=[(c[0], c[1]) for c in categorias],
        format_func=lambda x: x[1],
    )
    nombre_subcategoria = st.text_input("Nombre de la Subcategoría")

    if st.button("Agregar Subcategoría"):
        if nombre_subcategoria:
            agregar_subcategoria(categoria_seleccionada[0], nombre_subcategoria)
            # Actualizar datos JSON
            for categoria in datos_json["categorias"]:
                if categoria["id_categoria"] == categoria_seleccionada[0]:
                    categoria["subcategorias"].append(
                        {
                            "id_subcategoria": len(categoria["subcategorias"]) + 1,
                            "nombre_subcategoria": nombre_subcategoria,
                        }
                    )
            guardar_datos_json(datos_json)
            st.success("Subcategoría agregada correctamente.")
        else:
            st.error("Debe ingresar un nombre para la subcategoría.")

elif opcion == "Agregar Usuarios":
    st.header("Agregar Nuevo Usuario")
    nombre_usuario = st.text_input("Nombre del Usuario")

    if st.button("Agregar Usuario"):
        if nombre_usuario:
            agregar_usuario(nombre_usuario)
            datos_json["usuarios"].append(
                {
                    "id_usuario": len(datos_json["usuarios"]) + 1,
                    "nombre": nombre_usuario,
                }
            )
            guardar_datos_json(datos_json)
            st.success("Usuario agregado correctamente.")
        else:
            st.error("Debe ingresar un nombre para el usuario.")
