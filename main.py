import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Conexión a la base de datos SQLite
DB_PATH = "finanzas.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


# Funciones para interactuar con la base de datos
def get_usuarios():
    with get_connection() as conn:
        return conn.execute("SELECT id_usuario, nombre FROM usuarios").fetchall()


def get_categorias():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id_categoria, nombre_categoria, tipo FROM categorias"
        ).fetchall()


def get_subcategorias(id_categoria=None):
    with get_connection() as conn:
        query = "SELECT id_subcategoria, nombre_subcategoria FROM subcategorias"
        params = []
        if id_categoria:
            query += " WHERE id_categoria = ?"
            params.append(id_categoria)
        return conn.execute(query, params).fetchall()


def insert_transaccion(fecha, tipo, monto, id_subcategoria, descripcion, id_usuario):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transacciones (fecha, tipo, monto, id_subcategoria, descripcion, id_usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (fecha, tipo, monto, id_subcategoria, descripcion, id_usuario),
        )
        conn.commit()


def get_transacciones():
    with get_connection() as conn:
        result = conn.execute(
            """
            SELECT t.fecha, t.tipo, t.monto, s.nombre_subcategoria, c.nombre_categoria, u.nombre, t.descripcion
            FROM transacciones t
            JOIN subcategorias s ON t.id_subcategoria = s.id_subcategoria
            JOIN categorias c ON s.id_categoria = c.id_categoria
            JOIN usuarios u ON t.id_usuario = u.id_usuario
        """
        ).fetchall()
        result = [list(row) for row in result]
        for row in result:
            row[2] = f"S/. {row[2]:,.2f}"
        # convertir a dataframe
        df = pd.DataFrame(
            result,
            columns=[
                "Fecha",
                "Tipo",
                "Monto",
                "Subcategoría",
                "Categoría",
                "Usuario",
                "Descripción",
            ],
        )
        return df


# Interfaz de Streamlit
st.title("Gestión de Ingresos y Gastos")

menu = st.sidebar.selectbox("Menú", ["Registrar Transacción", "Ver Transacciones"])

if menu == "Registrar Transacción":
    st.header("Registrar Transacción")

    # Selección de usuario
    usuarios = get_usuarios()
    usuario = st.selectbox(
        "Usuario", [(u[0], u[1]) for u in usuarios], format_func=lambda x: x[1]
    )
    id_usuario = usuario[0]

    # Selección de tipo
    tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])

    # Selección de categoría
    categorias = [c for c in get_categorias() if c[2] == tipo]
    categoria = st.selectbox("Categoría", categorias, format_func=lambda x: x[1])
    id_categoria = categoria[0]

    # Selección de subcategoría
    subcategorias = get_subcategorias(id_categoria)
    subcategoria = st.selectbox(
        "Subcategoría", subcategorias, format_func=lambda x: x[1]
    )
    id_subcategoria = subcategoria[0]

    # Datos de la transacción
    monto = st.number_input("Monto", min_value=0.0, step=0.01, format="%.2f")
    descripcion = st.text_area("Descripción")
    fecha = st.date_input("Fecha", datetime.now())

    if st.button("Guardar Transacción"):
        insert_transaccion(
            fecha.strftime("%Y-%m-%d"),
            tipo,
            monto,
            id_subcategoria,
            descripcion,
            id_usuario,
        )
        st.success("¡Transacción registrada con éxito!")

elif menu == "Ver Transacciones":
    st.header("Ver Transacciones")
    transacciones = get_transacciones()

    # Mostrar en una tabla
    st.dataframe(
        transacciones,
        use_container_width=True,
        hide_index=True,
    )
