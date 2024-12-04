import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import pytz
import os
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

# Cargar variables de entorno
load_dotenv()

# URL de la API de Google Apps Script
GOOGLE_SHEET_API_URL = os.getenv("GOOGLE_SHEET_API_URL")

# Conexión con la base de datos SQLite (Finanzas.db)
DATABASE_URL = "sqlite:///finanzas.db"
engine = create_engine(DATABASE_URL)

# Crear una clase base para el ORM
Base = declarative_base()

# Definición de modelos ORM


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)


class Categoria(Base):
    __tablename__ = "categorias"

    id_categoria = Column(Integer, primary_key=True, autoincrement=True)
    nombre_categoria = Column(String, nullable=False)
    tipo = Column(Enum("Ingreso", "Gasto", name="tipo_categoria"), nullable=False)


class Subcategoria(Base):
    __tablename__ = "subcategorias"

    id_subcategoria = Column(Integer, primary_key=True, autoincrement=True)
    id_categoria = Column(
        Integer, ForeignKey("categorias.id_categoria"), nullable=False
    )
    nombre_subcategoria = Column(String, nullable=False)

    categoria = relationship("Categoria", backref="subcategorias")


class Transaccion(Base):
    __tablename__ = "transacciones"

    id_transaccion = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    tipo = Column(Enum("Ingreso", "Gasto", name="tipo_transaccion"), nullable=False)
    monto = Column(Float, nullable=False)
    id_subcategoria = Column(
        Integer, ForeignKey("subcategorias.id_subcategoria"), nullable=False
    )
    descripcion = Column(String)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    subcategoria = relationship("Subcategoria", backref="transacciones")
    usuario = relationship("Usuario", backref="transacciones")


# Función para obtener la fecha y hora precisa en la zona horaria de Perú
def get_peru_time():
    peru_tz = pytz.timezone("America/Lima")
    return datetime.now(peru_tz).strftime("%Y-%m-%d %H:%M:%S")


# Función para enviar datos a la hoja de Google Sheets
def send_to_google_sheet(data: List[BaseModel]):
    """
    Envía los datos a la Google Sheet mediante la API de Google Apps Script.
    :param data: Lista de registros con toda la información.
    """
    # Asegúrate de convertir los objetos Pydantic en diccionarios
    data_dicts = [
        record.model_dump() for record in data
    ]  # Convertir cada objeto en un diccionario

    # Enviar los datos como una lista de diccionarios
    response = requests.post(GOOGLE_SHEET_API_URL, json=data_dicts)

    if response.status_code == 200:
        print("Datos enviados con éxito a la Google Sheet.")
    else:
        print(f"Error al enviar datos: {response.status_code}, {response.text}")


# Crear una sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def insert_transaccion(fecha, tipo, monto, id_subcategoria, descripcion, id_usuario):
    # Crear una nueva sesión
    db = SessionLocal()

    try:
        # Crear la transacción
        transaccion = Transaccion(
            fecha=fecha,
            tipo=tipo,
            monto=monto,
            descripcion=descripcion,
            id_subcategoria=id_subcategoria,
            id_usuario=id_usuario,
        )
        db.add(transaccion)
        db.commit()

        # Obtener los detalles de la transacción (subcategoría, categoría, etc.)
        transaccion_db = (
            db.query(Transaccion)
            .filter(Transaccion.id_transaccion == transaccion.id_transaccion)
            .first()
        )

        if transaccion_db:
            subcategoria = transaccion_db.subcategoria.nombre_subcategoria
            categoria = transaccion_db.subcategoria.categoria.nombre_categoria
            usuario = transaccion_db.usuario.nombre

            # Verificar los valores antes de crear el Pydantic
            # print(
            #    f"Subcategoría: {subcategoria}, Categoría: {categoria}, Usuario: {usuario}"
            # )

            # Pydantic model para la transacción
            transaccion_pydantic = TransaccionPydantic(
                fecha=fecha,
                tipo=tipo,
                monto=monto,
                descripcion=descripcion,
                subcategoria=subcategoria,
                categoria=categoria,
                usuario=usuario,
            )
            # Verificar si el modelo Pydantic tiene datos válidos
            # print(f"Datos a enviar: {transaccion_pydantic.model_dump()}")

            send_to_google_sheet([transaccion_pydantic])
            # print(transaccion_pydantic.model_dump())

    finally:
        db.close()


# Función para obtener los usuarios
def get_usuarios():
    db = SessionLocal()
    try:
        return db.query(Usuario).all()
    finally:
        db.close()


# Función para obtener las categorías
def get_categorias():
    db = SessionLocal()
    try:
        return db.query(Categoria).all()
    finally:
        db.close()


# Función para obtener las subcategorías por categoría
def get_subcategorias(id_categoria=None):
    db = SessionLocal()
    try:
        if id_categoria:
            return (
                db.query(Subcategoria)
                .filter(Subcategoria.id_categoria == id_categoria)
                .all()
            )
        return db.query(Subcategoria).all()
    finally:
        db.close()


# Función para obtener las transacciones completas
def get_full_transacciones():
    db = SessionLocal()
    try:
        result = (
            db.query(Transaccion).join(Subcategoria).join(Categoria).join(Usuario).all()
        )
        return [
            {
                "id_transaccion": t.id_transaccion,
                "fecha": t.fecha,
                "tipo": t.tipo,
                "monto": t.monto,
                "descripcion": t.descripcion,
                "nombre_subcategoria": t.subcategoria.nombre_subcategoria,
                "nombre_categoria": t.subcategoria.categoria.nombre_categoria,
                "usuario": t.usuario.nombre,
            }
            for t in result
        ]
    finally:
        db.close()


# Definición de modelos Pydantic


class TransaccionPydantic(BaseModel):
    fecha: str
    tipo: str
    monto: float
    descripcion: str
    subcategoria: str
    categoria: str
    usuario: str


class CategoriaPydantic(BaseModel):
    id_categoria: int
    nombre_categoria: str
    tipo: str


class SubcategoriaPydantic(BaseModel):
    id_subcategoria: int
    nombre_subcategoria: str


class UsuarioPydantic(BaseModel):
    id_usuario: int
    nombre: str


# Interfaz de Streamlit
st.title("Gestión de Ingresos y Gastos")

menu = st.sidebar.selectbox("Menú", ["Registrar Transacción", "Ver Transacciones"])

if menu == "Registrar Transacción":
    st.header("Registrar Transacción")

    # Selección de usuario
    usuarios = get_usuarios()
    usuario = st.selectbox(
        "Usuario",
        [(u.id_usuario, u.nombre) for u in usuarios],
        format_func=lambda x: x[1],
    )
    id_usuario = usuario[0]

    # Selección de tipo (Ingreso o Gasto)
    tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])

    # Selección de categoría
    categorias = [c for c in get_categorias() if c.tipo == tipo]
    categoria = st.selectbox(
        "Categoría", categorias, format_func=lambda x: x.nombre_categoria
    )
    id_categoria = categoria.id_categoria

    # Selección de subcategoría
    subcategorias = get_subcategorias(id_categoria)
    subcategoria = st.selectbox(
        "Subcategoría", subcategorias, format_func=lambda x: x.nombre_subcategoria
    )
    id_subcategoria = subcategoria.id_subcategoria

    # Datos de la transacción
    monto = st.number_input("Monto", min_value=0.0, step=0.01, format="%.2f")
    descripcion = st.text_area("Descripción")
    fecha = get_peru_time()  # Obtener la hora y fecha precisa en zona horaria de Perú

    if st.button("Guardar Transacción"):
        insert_transaccion(
            fecha,
            tipo,
            monto,
            id_subcategoria,
            descripcion,
            id_usuario,
        )
        st.success("¡Transacción registrada con éxito!")

elif menu == "Ver Transacciones":
    st.header("Ver Transacciones")
    transacciones = get_full_transacciones()

    # Mostrar en una tabla
    st.dataframe(
        transacciones,
        use_container_width=True,
        hide_index=True,
    )
