# auditoria.py
# ══════════════════════════════════════════════════════════════════
#  MÓDULO DE AUDITORÍA
#  Tarea 2: Auditoría
#
#  ¿Qué hace esto?
#  Guarda un registro de CADA acción importante que hace un usuario:
#  quién la hizo, qué hizo, cuándo y sobre qué dato.
#
#  Ejemplo: "admin creó el producto Laptop el 2026-05-06 10:30"
# ══════════════════════════════════════════════════════════════════

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ══════════════════════════════════════════════
#  CREAR TABLA DE AUDITORÍA (se llama al iniciar)
# ══════════════════════════════════════════════

def crear_tabla_auditoria():
    """
    Crea la tabla 'auditoria' si no existe.
    Llama esta función desde database.py → inicializar_db()
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL DEFAULT (datetime('now')),
            usuario_id  INTEGER,
            usuario_nombre TEXT,
            accion      TEXT    NOT NULL,
            tabla       TEXT    NOT NULL,
            registro_id INTEGER,
            detalle     TEXT
        )
    """)
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════
#  REGISTRAR UNA ACCIÓN
# ══════════════════════════════════════════════

def registrar(usuario_id, usuario_nombre, accion, tabla, registro_id=None, detalle=""):
    """
    Guarda una acción en la tabla auditoria.

    Parámetros:
        usuario_id     : ID del usuario que hizo la acción (número)
        usuario_nombre : nombre del usuario (texto)
        accion         : qué hizo: 'CREAR', 'EDITAR', 'ELIMINAR', 'LOGIN', etc.
        tabla          : en qué tabla: 'productos', 'clientes', 'facturas', etc.
        registro_id    : ID del registro afectado (opcional)
        detalle        : descripción adicional (opcional)

    Ejemplo de uso:
        import auditoria
        auditoria.registrar(1, "admin", "CREAR", "productos", 5, "Creó: Laptop Dell")
    """
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO auditoria
               (fecha, usuario_id, usuario_nombre, accion, tabla, registro_id, detalle)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                usuario_id,
                usuario_nombre,
                accion,
                tabla,
                registro_id,
                detalle,
            )
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[AUDITORÍA] Error al registrar: {e}")


# ══════════════════════════════════════════════
#  CONSULTAR EL HISTORIAL
# ══════════════════════════════════════════════

def obtener_historial(limite=200):
    """
    Devuelve los últimos registros de auditoría.
    'limite' es cuántos registros traer (por defecto 200).
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM auditoria
               ORDER BY id DESC
               LIMIT ?""",
            (limite,)
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[AUDITORÍA] Error al obtener historial: {e}")
        return []


def obtener_historial_por_usuario(usuario_id, limite=100):
    """Devuelve el historial de un usuario específico."""
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM auditoria
               WHERE usuario_id=?
               ORDER BY id DESC LIMIT ?""",
            (usuario_id, limite)
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[AUDITORÍA] Error: {e}")
        return []


def obtener_historial_por_tabla(tabla, limite=100):
    """Devuelve el historial de cambios en una tabla específica."""
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM auditoria
               WHERE tabla=?
               ORDER BY id DESC LIMIT ?""",
            (tabla, limite)
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[AUDITORÍA] Error: {e}")
        return []