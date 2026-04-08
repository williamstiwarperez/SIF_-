import sqlite3
import os
import hashlib

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")

# ══════════════════════════════════════════════════════════════════════════════
#  CONEXIÓN
# ══════════════════════════════════════════════════════════════════════════════
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ══════════════════════════════════════════════════════════════════════════════
#  INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def inicializar_db():
    conn = get_connection()
    cur = conn.cursor()

    # ── Tablas ──────────────────────────────────────────────────────────────
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
            precio   REAL    NOT NULL DEFAULT 0  CHECK(precio   >= 0),
            cantidad INTEGER NOT NULL DEFAULT 0  CHECK(cantidad >= 0),
            codigo   TEXT    DEFAULT '',
            marca    TEXT    DEFAULT '',
            detalles TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS facturas (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha   TEXT    NOT NULL,
            total   REAL    NOT NULL DEFAULT 0,
            cliente TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS detalle_factura (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id      INTEGER NOT NULL
                                REFERENCES facturas(id) ON DELETE CASCADE,
            producto_id     INTEGER NOT NULL
                                REFERENCES productos(id),
            cantidad        INTEGER NOT NULL CHECK(cantidad > 0),
            precio_unitario REAL    NOT NULL CHECK(precio_unitario >= 0),
            total           REAL    NOT NULL
        );

        -- ── CORRECCIÓN ③: Índices para acelerar búsquedas ──────────────────
        -- Sin estos índices, SQLite hace "full scan" en cada búsqueda.
        -- Con ellos, las consultas frecuentes son instantáneas.
        CREATE INDEX IF NOT EXISTS idx_productos_nombre   ON productos(nombre);
        CREATE INDEX IF NOT EXISTS idx_productos_codigo   ON productos(codigo);
        CREATE INDEX IF NOT EXISTS idx_facturas_cliente   ON facturas(cliente);
        CREATE INDEX IF NOT EXISTS idx_facturas_fecha     ON facturas(fecha);
        CREATE INDEX IF NOT EXISTS idx_detalle_factura_id ON detalle_factura(factura_id);
    """)

    # Usuario admin por defecto
    cur.execute(
        "INSERT OR IGNORE INTO usuarios (usuario, contraseña, rol) VALUES (?,?,?)",
        ("admin", _hash("admin123"), "admin"),
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES INTERNAS
# ══════════════════════════════════════════════════════════════════════════════

def _hash(password: str) -> str:
    """SHA-256 del password. Nunca se guarda la contraseña en texto plano."""
    return hashlib.sha256(password.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
#  USUARIOS
# ══════════════════════════════════════════════════════════════════════════════

def autenticar_usuario(usuario: str, contraseña: str):
    """
    Verifica credenciales.
    Retorna sqlite3.Row del usuario si son correctas, o None.

    Ejemplo:
        row = autenticar_usuario("admin", "admin123")
        if row:
            print(row["rol"])   # "admin"
    """
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND contraseña=?",
            (usuario, _hash(contraseña)),
        ).fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"[DB] autenticar_usuario: {e}")
        return None


def obtener_usuarios():
    """Devuelve todos los usuarios (sin contraseña por seguridad)."""
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, usuario, rol FROM usuarios ORDER BY id"
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_usuarios: {e}")
        return []


def crear_usuario(usuario: str, contraseña: str, rol: str):
    """
    Inserta un nuevo usuario.
    Retorna (True, 'mensaje') o (False, 'error').

    Ejemplo:
        ok, msg = crear_usuario("vendedor1", "pass123", "vendedor")
    """
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO usuarios (usuario, contraseña, rol) VALUES (?,?,?)",
            (usuario, _hash(contraseña), rol),
        )
        conn.commit()
        conn.close()
        return True, "Usuario creado correctamente."
    except sqlite3.IntegrityError:
        return False, f"El usuario '{usuario}' ya existe."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_usuario(uid: int, usuario: str, contraseña: str, rol: str):
    """
    Actualiza datos de un usuario.
    Si contraseña está vacía, no la modifica (permite cambiar solo el rol).
    """
    try:
        conn = get_connection()
        if contraseña:
            conn.execute(
                "UPDATE usuarios SET usuario=?, contraseña=?, rol=? WHERE id=?",
                (usuario, _hash(contraseña), rol, uid),
            )
        else:
            conn.execute(
                "UPDATE usuarios SET usuario=?, rol=? WHERE id=?",
                (usuario, rol, uid),
            )
        conn.commit()
        conn.close()
        return True, "Usuario actualizado."
    except sqlite3.IntegrityError:
        return False, f"El nombre '{usuario}' ya está en uso."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_usuario(uid: int):
    """Elimina un usuario por su ID."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        return True, "Usuario eliminado."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCTOS
# ══════════════════════════════════════════════════════════════════════════════

def obtener_productos(filtro: str = ""):
    """
    Lista productos filtrando por nombre o código.
    filtro="" devuelve todos los productos.

    Ejemplo — consultar productos:
        todos   = obtener_productos()
        sillas  = obtener_productos("silla")
        por_cod = obtener_productos("DELL-001")
    """
    try:
        conn = get_connection()
        patron = f"%{filtro}%"
        rows = conn.execute(
            """SELECT * FROM productos
               WHERE nombre LIKE ? OR codigo LIKE ?
               ORDER BY nombre""",
            (patron, patron),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_productos: {e}")
        return []


def obtener_producto_por_id(pid: int):
    """
    Busca un producto por su ID.
    Retorna sqlite3.Row o None si no existe.
    """
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM productos WHERE id=?", (pid,)
        ).fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"[DB] obtener_producto_por_id: {e}")
        return None


def crear_producto(nombre: str, precio: float, cantidad: int,
                   codigo: str, marca: str, detalles: str):
    """
    Inserta un producto nuevo.
    Retorna (True, 'mensaje') o (False, 'error').

    Ejemplo — insertar producto:
        ok, msg = crear_producto(
            nombre   = "Laptop Dell Inspiron",
            precio   = 850.0,
            cantidad = 10,
            codigo   = "DELL-001",
            marca    = "Dell",
            detalles = "Core i5, 8GB RAM"
        )
    """
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO productos (nombre, precio, cantidad, codigo, marca, detalles)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nombre, precio, cantidad, codigo, marca, detalles),
        )
        conn.commit()
        conn.close()
        return True, "Producto creado correctamente."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_producto(pid: int, nombre: str, precio: float, cantidad: int,
                        codigo: str, marca: str, detalles: str):
    """
    Actualiza todos los campos de un producto.

    Ejemplo — actualizar inventario manualmente:
        ok, msg = actualizar_producto(1, "Laptop Dell i7", 950.0, 8,
                                      "DELL-001", "Dell", "Core i7")
    """
    try:
        conn = get_connection()
        conn.execute(
            """UPDATE productos
               SET nombre=?, precio=?, cantidad=?, codigo=?, marca=?, detalles=?
               WHERE id=?""",
            (nombre, precio, cantidad, codigo, marca, detalles, pid),
        )
        conn.commit()
        conn.close()
        return True, "Producto actualizado."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_producto(pid: int):
    """
    Elimina un producto por su ID.
    CORRECCIÓN ⑦: captura IntegrityError con mensaje claro cuando hay
    facturas que referencian al producto.
    """
    try:
        conn = get_connection()
        conn.execute("DELETE FROM productos WHERE id=?", (pid,))
        conn.commit()
        conn.close()
        return True, "Producto eliminado."
    except sqlite3.IntegrityError:
        return False, "No se puede eliminar: el producto tiene facturas asociadas."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════════════════
#  FACTURAS  ←  operación más importante del sistema
# ══════════════════════════════════════════════════════════════════════════════

def crear_factura(fecha: str, total: float, cliente: str, items: list):
    """
    Registra una factura completa en una TRANSACCIÓN ATÓMICA.

    CORRECCIÓN ②: la versión original no tenía rollback.
    Si fallaba al insertar el ítem 3 de 5, los ítems 1 y 2 quedaban
    guardados pero el stock ya estaba descontado → datos inconsistentes.
    Ahora si CUALQUIER paso falla, NADA se guarda (rollback completo).

    Pasos dentro de la transacción:
      1. Inserta cabecera en 'facturas'
      2. Por cada ítem:
         a. Verifica que el producto existe
         b. Verifica que hay stock suficiente
         c. Inserta línea en 'detalle_factura'
         d. Descuenta stock en 'productos'
      3. Si todo OK  → COMMIT  (se guarda todo)
         Si algo falla → ROLLBACK (no se guarda nada)

    Parámetros:
      fecha   : str   — formato "2026-03-25"
      total   : float — suma total de la factura
      cliente : str   — nombre del cliente
      items   : list  — lista de dicts con claves:
                        { producto_id, cantidad, precio_unitario, total }

    Retorna (True, factura_id) o (False, "mensaje de error")

    Ejemplo — registrar factura:
        items = [
            {"producto_id": 2, "cantidad": 1,
             "precio_unitario": 22000.0, "total": 22000.0},
        ]
        ok, resultado = crear_factura("2026-04-08", 22000.0, "Juan Pérez", items)
        if ok:
            print(f"Factura #{resultado} generada")
    """
    conn = get_connection()
    try:
        # PASO 1 — Cabecera de factura
        cur = conn.execute(
            "INSERT INTO facturas (fecha, total, cliente) VALUES (?, ?, ?)",
            (fecha, total, cliente),
        )
        factura_id = cur.lastrowid

        # PASO 2 — Líneas de detalle + descuento de stock
        for item in items:
            pid      = item["producto_id"]
            cant     = item["cantidad"]
            p_unit   = item["precio_unitario"]
            subtotal = item["total"]

            # ── Validar stock dentro de la transacción ──────────────────────
            stock_row = conn.execute(
                "SELECT cantidad, nombre FROM productos WHERE id=?", (pid,)
            ).fetchone()

            if stock_row is None:
                raise ValueError(f"El producto con ID {pid} no existe.")

            if stock_row["cantidad"] < cant:
                raise ValueError(
                    f"Stock insuficiente para '{stock_row['nombre']}'. "
                    f"Disponible: {stock_row['cantidad']}, solicitado: {cant}."
                )

            # ── Insertar línea de detalle ────────────────────────────────────
            conn.execute(
                """INSERT INTO detalle_factura
                   (factura_id, producto_id, cantidad, precio_unitario, total)
                   VALUES (?, ?, ?, ?, ?)""",
                (factura_id, pid, cant, p_unit, subtotal),
            )

            # ── Descontar stock ──────────────────────────────────────────────
            conn.execute(
                "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
                (cant, pid),
            )

        # PASO 3 — Guardar todo
        conn.commit()
        return True, factura_id

    except (sqlite3.Error, ValueError) as e:
        conn.rollback()   # ← NADA se guarda si algo falló
        return False, str(e)
    finally:
        conn.close()


def obtener_facturas(filtro: str = ""):
    """
    Lista facturas filtrando por cliente o número de factura.
    Orden: más reciente primero.

    Ejemplo — consultar facturas:
        todas      = obtener_facturas()
        de_juan    = obtener_facturas("juan")
        factura_5  = obtener_facturas("5")
    """
    try:
        conn = get_connection()
        patron = f"%{filtro}%"
        rows = conn.execute(
            """SELECT * FROM facturas
               WHERE cliente LIKE ? OR CAST(id AS TEXT) LIKE ?
               ORDER BY id DESC""",
            (patron, patron),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_facturas: {e}")
        return []


def obtener_detalle_factura(factura_id: int):
    """
    Devuelve todas las líneas de una factura con el nombre del producto.

    Ejemplo:
        detalles = obtener_detalle_factura(1)
        for d in detalles:
            print(d["nombre"], d["cantidad"], d["total"])
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT df.id,
                      df.factura_id,
                      df.cantidad,
                      df.precio_unitario,
                      df.total,
                      p.nombre,
                      p.codigo
               FROM detalle_factura df
               JOIN productos p ON p.id = df.producto_id
               WHERE df.factura_id = ?
               ORDER BY df.id""",
            (factura_id,),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_detalle_factura: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════════════════════

def reporte_resumen():
    """
    Métricas generales para el Dashboard.

    CORRECCIÓN ⑤: la versión original devolvía {} en caso de error,
    causando KeyError en el dashboard. Ahora devuelve valores por defecto.

    Retorna dict con:
      total_productos : int
      total_facturas  : int
      bajo_stock      : int   (productos con cantidad <= 5)
      ventas_mes      : float (suma de facturas del mes en curso)
    """
    try:
        conn = get_connection()

        total_productos = conn.execute(
            "SELECT COUNT(*) FROM productos"
        ).fetchone()[0]

        total_facturas = conn.execute(
            "SELECT COUNT(*) FROM facturas"
        ).fetchone()[0]

        bajo_stock = conn.execute(
            "SELECT COUNT(*) FROM productos WHERE cantidad <= 5"
        ).fetchone()[0]

        ventas_mes = conn.execute(
            """SELECT COALESCE(SUM(total), 0)
               FROM facturas
               WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')"""
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
        # CORRECCIÓN ⑤: devuelve ceros en lugar de {} para evitar KeyError
        return {
            "total_productos": 0,
            "total_facturas":  0,
            "bajo_stock":      0,
            "ventas_mes":      0.0,
        }


def reporte_ventas_por_producto():
    """
    Top 10 productos más vendidos ordenados por ingresos.
    Retorna lista de Rows con: nombre, unidades, ingresos.
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT p.nombre,
                      SUM(df.cantidad) AS unidades,
                      SUM(df.total)    AS ingresos
               FROM detalle_factura df
               JOIN productos p ON p.id = df.producto_id
               GROUP BY p.id
               ORDER BY ingresos DESC
               LIMIT 10"""
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] reporte_ventas_por_producto: {e}")
        return []


def reporte_productos_bajo_stock(limite: int = 5):
    """
    CORRECCIÓN ⑥: función nueva para alertas de reabastecimiento.
    Lista productos con stock <= limite, ordenados de menor a mayor.

    Ejemplo:
        criticos = reporte_productos_bajo_stock(3)
        for p in criticos:
            print(f"{p['nombre']}: {p['cantidad']} unidades")
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT id, nombre, cantidad, codigo, marca
               FROM productos
               WHERE cantidad <= ?
               ORDER BY cantidad ASC""",
            (limite,),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] reporte_productos_bajo_stock: {e}")
        return []
    