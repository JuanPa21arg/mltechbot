# crear_db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    correo = Column(String(100), unique=True)
    contraseña = Column(String(100), nullable=False)
    es_admin = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

class PerfilNegocio(Base):
    __tablename__ = 'perfil_negocio'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'), unique=True)
    nombre = Column(String(100))
    servicios = Column(String(300))
    horarios = Column(String(100))
    ubicacion = Column(String(100))
    estilo = Column(String(100))

class Respuesta(Base):
    __tablename__ = 'respuesta'
    id = Column(Integer, primary_key=True)
    mensaje = Column(String(100), nullable=False)
    respuesta = Column(String(300), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)

# Crear engine y base
engine = create_engine('sqlite:///respuestas.db')
Base.metadata.create_all(engine)

print("✅ Base de datos 'respuestas.db' creada correctamente.")
