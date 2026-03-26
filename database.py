# Maneja toda la conexión a SQLite y las operaciones SQL.

import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.db")

def get_connection():
# Devuelve una conexión SQLite con row_factory para acceso por nombre.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db():
    """Crea todas las tablas si no existen y siembra el usuario admin."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario    TEXT    NOT NULL UNIQUE,
            contraseña TEXT    NOT NULL,
            rol        TEXT    NOT NULL CHECK(rol IN ('admin','vendedor'))
        );

        CREATE TABLE IF NOT EXISTS productos (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT    NOT NULL,
            precio   REAL    NOT NULL DEFAULT 0,
            cantidad INTEGER NOT NULL DEFAULT 0,
            codigo   TEXT,
            marca    TEXT,
            detalles TEXT
        );

        CREATE TABLE IF NOT EXISTS facturas (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha  TEXT    NOT NULL,
            total  REAL    NOT NULL DEFAULT 0,
            cliente TEXT   DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS detalle_factura (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id      INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
            producto_id     INTEGER NOT NULL REFERENCES productos(id),
            cantidad        INTEGER NOT NULL,
            precio_unitario REAL    NOT NULL,
            total           REAL    NOT NULL
        );
    """)

    # Crear usuario admin por defecto si no existe
    pwd_hash = _hash("admin123")
    cur.execute(
        "INSERT OR IGNORE INTO usuarios (usuario, contraseña, rol) VALUES (?,?,?)",
        ("admin", pwd_hash, "admin"),
    )
    conn.commit()
    conn.close()


# ──────────────────────────── USUARIOS ────────────────────────────

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def autenticar_usuario(usuario: str, contraseña: str):
    """Devuelve el Row del usuario si las credenciales son correctas, o None."""
    try:
        conn = get_connection()
        cur = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND contraseña=?",
            (usuario, _hash(contraseña)),
        )
        row = cur.fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"[DB] autenticar_usuario: {e}")
        return None


def obtener_usuarios():
    try:
        conn = get_connection()
        rows = conn.execute("SELECT id,usuario,rol FROM usuarios ORDER BY id").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_usuarios: {e}")
        return []


def crear_usuario(usuario: str, contraseña: str, rol: str):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO usuarios (usuario,contraseña,rol) VALUES (?,?,?)",
            (usuario, _hash(contraseña), rol),
        )
        conn.commit()
        conn.close()
        return True, "Usuario creado."
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_usuario(uid: int, usuario: str, contraseña: str, rol: str):
    try:
        conn = get_connection()
        if contraseña:
            conn.execute(
                "UPDATE usuarios SET usuario=?,contraseña=?,rol=? WHERE id=?",
                (usuario, _hash(contraseña), rol, uid),
            )
        else:
            conn.execute(
                "UPDATE usuarios SET usuario=?,rol=? WHERE id=?",
                (usuario, rol, uid),
            )
        conn.commit()
        conn.close()
        return True, "Usuario actualizado."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_usuario(uid: int):
    try:
        conn = get_connection()
        conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        return True, "Usuario eliminado."
    except sqlite3.Error as e:
        return False, str(e)


# ──────────────────────────── PRODUCTOS ────────────────────────────

def obtener_productos(filtro: str = ""):
    try:
        conn = get_connection()
        q = "%{}%".format(filtro)
        rows = conn.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? OR codigo LIKE ? ORDER BY nombre",
            (q, q),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_productos: {e}")
        return []


def obtener_producto_por_id(pid: int):
    try:
        conn = get_connection()
        row = conn.execute("SELECT * FROM productos WHERE id=?", (pid,)).fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"[DB] obtener_producto_por_id: {e}")
        return None


def crear_producto(nombre, precio, cantidad, codigo, marca, detalles):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO productos (nombre,precio,cantidad,codigo,marca,detalles) VALUES (?,?,?,?,?,?)",
            (nombre, precio, cantidad, codigo, marca, detalles),
        )
        conn.commit()
        conn.close()
        return True, "Producto creado."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_producto(pid, nombre, precio, cantidad, codigo, marca, detalles):
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE productos SET nombre=?,precio=?,cantidad=?,codigo=?,marca=?,detalles=? WHERE id=?",
            (nombre, precio, cantidad, codigo, marca, detalles, pid),
        )
        conn.commit()
        conn.close()
        return True, "Producto actualizado."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_producto(pid: int):
    try:
        conn = get_connection()
        conn.execute("DELETE FROM productos WHERE id=?", (pid,))
        conn.commit()
        conn.close()
        return True, "Producto eliminado."
    except sqlite3.Error as e:
        return False, str(e)


def reducir_stock(pid: int, cantidad: int):
    """Descuenta stock; devuelve (ok, mensaje)."""
    try:
        conn = get_connection()
        row = conn.execute("SELECT cantidad FROM productos WHERE id=?", (pid,)).fetchone()
        if row is None:
            conn.close()
            return False, "Producto no encontrado."
        if row["cantidad"] < cantidad:
            conn.close()
            return False, "Stock insuficiente."
        conn.execute(
            "UPDATE productos SET cantidad=cantidad-? WHERE id=?", (cantidad, pid)
        )
        conn.commit()
        nuevo_stock = conn.execute("SELECT cantidad FROM productos WHERE id=?", (pid,)).fetchone()["cantidad"]
        conn.close()
        return True, nuevo_stock
    except sqlite3.Error as e:
        return False, str(e)


# ──────────────────────────── FACTURAS ────────────────────────────

def crear_factura(fecha: str, total: float, cliente: str, items: list):
    """
    items: lista de dicts {producto_id, cantidad, precio_unitario, total}
    Retorna (ok, factura_id o mensaje)
    """
    try:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO facturas (fecha,total,cliente) VALUES (?,?,?)",
            (fecha, total, cliente),
        )
        factura_id = cur.lastrowid
        for it in items:
            conn.execute(
                "INSERT INTO detalle_factura (factura_id,producto_id,cantidad,precio_unitario,total) VALUES (?,?,?,?,?)",
                (factura_id, it["producto_id"], it["cantidad"], it["precio_unitario"], it["total"]),
            )
            # Reducir stock
            conn.execute(
                "UPDATE productos SET cantidad=cantidad-? WHERE id=?",
                (it["cantidad"], it["producto_id"]),
            )
        conn.commit()
        conn.close()
        return True, factura_id
    except sqlite3.Error as e:
        return False, str(e)


def obtener_facturas(filtro: str = ""):
    try:
        conn = get_connection()
        q = "%{}%".format(filtro)
        rows = conn.execute(
            "SELECT * FROM facturas WHERE cliente LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY id DESC",
            (q, q),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_facturas: {e}")
        return []


def obtener_detalle_factura(factura_id: int):
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT df.*, p.nombre FROM detalle_factura df
               JOIN productos p ON p.id=df.producto_id
               WHERE df.factura_id=?""",
            (factura_id,),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_detalle_factura: {e}")
        return []


# ──────────────────────────── REPORTES ────────────────────────────

def reporte_resumen():
    """Devuelve métricas generales para el dashboard."""
    try:
        conn = get_connection()
        total_productos = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        total_facturas  = conn.execute("SELECT COUNT(*) FROM facturas").fetchone()[0]
        bajo_stock      = conn.execute("SELECT COUNT(*) FROM productos WHERE cantidad<=5").fetchone()[0]
        ventas_mes      = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM facturas WHERE strftime('%Y-%m',fecha)=strftime('%Y-%m','now')"
        ).fetchone()[0]
        conn.close()
        return {
            "total_productos": total_productos,
            "total_facturas":  total_facturas,
            "bajo_stock":      bajo_stock,
            "ventas_mes":      ventas_mes,
        }
    except sqlite3.Error as e:
        print(f"[DB] reporte_resumen: {e}")
        return {}


def reporte_ventas_por_producto():
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT p.nombre,
                      SUM(df.cantidad)         AS unidades,
                      SUM(df.total)            AS ingresos
               FROM detalle_factura df
               JOIN productos p ON p.id=df.producto_id
               GROUP BY p.id ORDER BY ingresos DESC LIMIT 10"""
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] reporte_ventas_por_producto: {e}")
        return []


