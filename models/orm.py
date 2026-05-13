# models/orm.py
# ══════════════════════════════════════════════════════════════════
#  ORM SIMPLE — Mapeo Objeto-Relacional
#  Tarea 1: Implementar ORM
#
#  ¿Qué hace esto?
#  En lugar de escribir SQL a mano, usamos clases Python.
#  Cada clase representa una tabla de la base de datos.
#  Ejemplo: la clase Producto representa la tabla "productos".
# ══════════════════════════════════════════════════════════════════

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "inventario.db")


def get_connection():
    """Abre la conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ──────────────────────────────────────────────
#  CLASE BASE — todos los modelos la heredan
# ──────────────────────────────────────────────

class ModeloBase:
    """
    Clase base con operaciones comunes para todos los modelos.
    'tabla' y 'campos' se definen en cada subclase.
    """
    tabla = ""    # nombre de la tabla en SQLite
    campos = []   # lista de columnas (sin 'id')

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", None)
        for campo in self.campos:
            setattr(self, campo, kwargs.get(campo, None))

    # ── Leer todos ────────────────────────────
    @classmethod
    def todos(cls, filtro=None):
        """Devuelve todos los registros de la tabla."""
        conn = get_connection()
        if filtro:
            q = f"%{filtro}%"
            col = cls.campos[0]  # busca en el primer campo (ej: nombre)
            rows = conn.execute(
                f"SELECT * FROM {cls.tabla} WHERE {col} LIKE ? ORDER BY {col}",
                (q,)
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {cls.tabla} ORDER BY {cls.campos[0]}"
            ).fetchall()
        conn.close()
        return [cls(**dict(r)) for r in rows]

    # ── Leer uno por ID ───────────────────────
    @classmethod
    def obtener(cls, id):
        """Devuelve un registro por su ID."""
        conn = get_connection()
        row = conn.execute(
            f"SELECT * FROM {cls.tabla} WHERE id=?", (id,)
        ).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    # ── Guardar (crear o actualizar) ──────────
    def guardar(self):
        """
        Si el objeto ya tiene ID → lo actualiza.
        Si NO tiene ID → crea un nuevo registro.
        """
        conn = get_connection()
        valores = [getattr(self, c) for c in self.campos]
        if self.id is None:
            # INSERT
            placeholders = ", ".join(["?"] * len(self.campos))
            cols = ", ".join(self.campos)
            cur = conn.execute(
                f"INSERT INTO {self.tabla} ({cols}) VALUES ({placeholders})",
                valores
            )
            self.id = cur.lastrowid
        else:
            # UPDATE
            sets = ", ".join([f"{c}=?" for c in self.campos])
            conn.execute(
                f"UPDATE {self.tabla} SET {sets} WHERE id=?",
                valores + [self.id]
            )
        conn.commit()
        conn.close()
        return True, f"Registro guardado correctamente (ID={self.id})."

    # ── Eliminar ──────────────────────────────
    def eliminar(self):
        """Elimina el registro de la base de datos."""
        if self.id is None:
            return False, "No hay ID para eliminar."
        conn = get_connection()
        conn.execute(f"DELETE FROM {self.tabla} WHERE id=?", (self.id,))
        conn.commit()
        conn.close()
        return True, "Registro eliminado."

    def __repr__(self):
        nombre = getattr(self, "nombre", getattr(self, "usuario", "?"))
        return f"<{self.__class__.__name__} id={self.id} nombre={nombre!r}>"


# ══════════════════════════════════════════════
#  MODELOS CONCRETOS
# ══════════════════════════════════════════════

class ProductoORM(ModeloBase):
    """Representa la tabla 'productos'."""
    tabla = "productos"
    campos = ["nombre", "precio", "cantidad", "codigo", "marca", "detalles", "categoria_id", "activo"]

    def esta_disponible(self):
        return self.cantidad > 0

    def nivel_stock(self):
        if self.cantidad == 0:
            return "Sin stock"
        if self.cantidad <= 5:
            return "Bajo stock"
        return "Disponible"


class ClienteORM(ModeloBase):
    """Representa la tabla 'clientes'."""
    tabla = "clientes"
    campos = ["nombre", "identificacion", "telefono", "email", "direccion", "creado_en"]


class UsuarioORM(ModeloBase):
    """Representa la tabla 'usuarios'."""
    tabla = "usuarios"
    campos = ["usuario", "contraseña", "rol", "activo", "creado_en"]

    def es_admin(self):
        return self.rol == "admin"


class CategoriaORM(ModeloBase):
    """Representa la tabla 'categorias'."""
    tabla = "categorias"
    campos = ["nombre", "descripcion"]


class ProveedorORM(ModeloBase):
    """Representa la tabla 'proveedores'."""
    tabla = "proveedores"
    campos = ["nombre", "contacto", "telefono", "email", "direccion", "activo"]