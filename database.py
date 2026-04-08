# database.py
# Maneja toda la conexión a SQLite y las operaciones SQL.
# Versión 2.0 — Modelo de datos profesional y escalable

import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.db")


def get_connection():
    """Devuelve una conexión SQLite con row_factory para acceso por nombre."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db():
    """Crea todas las tablas si no existen, índices, triggers y siembra datos base."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""

    -- ══════════════════════════════════════════════
    --  USUARIOS
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS usuarios (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario    TEXT    NOT NULL UNIQUE,
        contraseña TEXT    NOT NULL,
        rol        TEXT    NOT NULL CHECK(rol IN ('admin','vendedor')),
        activo     INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0, 1)),
        creado_en  TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ══════════════════════════════════════════════
    --  CLIENTES
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS clientes (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre       TEXT    NOT NULL,
        identificacion TEXT  UNIQUE,
        telefono     TEXT,
        email        TEXT,
        direccion    TEXT,
        creado_en    TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ══════════════════════════════════════════════
    --  CATEGORÍAS DE PRODUCTOS
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS categorias (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre      TEXT    NOT NULL UNIQUE,
        descripcion TEXT
    );

    -- ══════════════════════════════════════════════
    --  PROVEEDORES
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS proveedores (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre    TEXT    NOT NULL,
        contacto  TEXT,
        telefono  TEXT,
        email     TEXT,
        direccion TEXT,
        activo    INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
    );

    -- ══════════════════════════════════════════════
    --  MÉTODOS DE PAGO
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS metodos_pago (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT    NOT NULL UNIQUE
    );

    -- ══════════════════════════════════════════════
    --  PRODUCTOS
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS productos (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre       TEXT    NOT NULL,
        precio       REAL    NOT NULL DEFAULT 0,
        cantidad     INTEGER NOT NULL DEFAULT 0,
        codigo       TEXT    UNIQUE,
        marca        TEXT,
        detalles     TEXT,
        categoria_id INTEGER REFERENCES categorias(id) ON UPDATE CASCADE ON DELETE SET NULL,
        activo       INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
    );

    -- ══════════════════════════════════════════════
    --  FACTURAS
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS facturas (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha          TEXT    NOT NULL DEFAULT (datetime('now')),
        cliente_id     INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
        usuario_id     INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
        metodo_pago_id INTEGER REFERENCES metodos_pago(id) ON DELETE SET NULL,
        subtotal       REAL    NOT NULL DEFAULT 0,
        impuesto       REAL    NOT NULL DEFAULT 0,
        total          REAL    NOT NULL DEFAULT 0,
        cliente_nombre TEXT    DEFAULT '',
        estado         TEXT    NOT NULL DEFAULT 'completada' CHECK(estado IN ('completada','anulada'))
    );

    -- ══════════════════════════════════════════════
    --  DETALLE FACTURA
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS detalle_factura (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        factura_id      INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
        producto_id     INTEGER NOT NULL REFERENCES productos(id),
        cantidad        INTEGER NOT NULL,
        precio_unitario REAL    NOT NULL,
        subtotal        REAL    NOT NULL
    );

    -- ══════════════════════════════════════════════
    --  MOVIMIENTOS DE INVENTARIO
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS movimientos_inventario (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id  INTEGER NOT NULL REFERENCES productos(id),
        usuario_id   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
        tipo         TEXT    NOT NULL CHECK(tipo IN ('entrada','salida','ajuste')),
        cantidad     INTEGER NOT NULL,
        referencia   TEXT,           -- ej: 'FACTURA-12' o 'COMPRA-5'
        nota         TEXT,
        fecha        TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ══════════════════════════════════════════════
    --  COMPRAS (entradas por proveedor)
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS compras (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER REFERENCES proveedores(id) ON DELETE SET NULL,
        usuario_id   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
        fecha        TEXT    NOT NULL DEFAULT (datetime('now')),
        total        REAL    NOT NULL DEFAULT 0,
        estado       TEXT    NOT NULL DEFAULT 'recibida' CHECK(estado IN ('recibida','pendiente','cancelada'))
    );

    -- ══════════════════════════════════════════════
    --  DETALLE COMPRA
    -- ══════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS detalle_compra (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        compra_id       INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
        producto_id     INTEGER NOT NULL REFERENCES productos(id),
        cantidad        INTEGER NOT NULL,
        precio_unitario REAL    NOT NULL,
        subtotal        REAL    NOT NULL
    );


    -- ══════════════════════════════════════════════
    --  ÍNDICES
    -- ══════════════════════════════════════════════
    CREATE INDEX IF NOT EXISTS idx_productos_nombre     ON productos(nombre);
    CREATE INDEX IF NOT EXISTS idx_productos_codigo     ON productos(codigo);
    CREATE INDEX IF NOT EXISTS idx_productos_categoria  ON productos(categoria_id);
    CREATE INDEX IF NOT EXISTS idx_facturas_fecha       ON facturas(fecha);
    CREATE INDEX IF NOT EXISTS idx_facturas_cliente     ON facturas(cliente_id);
    CREATE INDEX IF NOT EXISTS idx_detalle_factura_fk   ON detalle_factura(factura_id);
    CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_inventario(producto_id);
    CREATE INDEX IF NOT EXISTS idx_movimientos_fecha    ON movimientos_inventario(fecha);
    CREATE INDEX IF NOT EXISTS idx_compras_proveedor    ON compras(proveedor_id);


    -- ══════════════════════════════════════════════
    --  TRIGGERS — actualización automática de stock
    -- ══════════════════════════════════════════════

    -- Al registrar una SALIDA en movimientos → descuenta stock
    CREATE TRIGGER IF NOT EXISTS trg_salida_stock
    AFTER INSERT ON movimientos_inventario
    WHEN NEW.tipo = 'salida'
    BEGIN
        UPDATE productos
        SET cantidad = cantidad - NEW.cantidad
        WHERE id = NEW.producto_id;
    END;

    -- Al registrar una ENTRADA en movimientos → suma stock
    CREATE TRIGGER IF NOT EXISTS trg_entrada_stock
    AFTER INSERT ON movimientos_inventario
    WHEN NEW.tipo = 'entrada'
    BEGIN
        UPDATE productos
        SET cantidad = cantidad + NEW.cantidad
        WHERE id = NEW.producto_id;
    END;

    -- Al insertar detalle_factura → crea movimiento de salida automático
    CREATE TRIGGER IF NOT EXISTS trg_venta_movimiento
    AFTER INSERT ON detalle_factura
    BEGIN
        INSERT INTO movimientos_inventario (producto_id, usuario_id, tipo, cantidad, referencia, nota)
        SELECT NEW.producto_id,
               f.usuario_id,
               'salida',
               NEW.cantidad,
               'FACTURA-' || NEW.factura_id,
               'Venta automática'
        FROM facturas f
        WHERE f.id = NEW.factura_id;
    END;

    -- Al insertar detalle_compra → crea movimiento de entrada automático
    CREATE TRIGGER IF NOT EXISTS trg_compra_movimiento
    AFTER INSERT ON detalle_compra
    BEGIN
        INSERT INTO movimientos_inventario (producto_id, usuario_id, tipo, cantidad, referencia, nota)
        SELECT NEW.producto_id,
               c.usuario_id,
               'entrada',
               NEW.cantidad,
               'COMPRA-' || NEW.compra_id,
               'Compra automática'
        FROM compras c
        WHERE c.id = NEW.compra_id;
    END;

    """)

    # ── Datos semilla ──────────────────────────────────────────────────────────

    # Usuario admin por defecto
    pwd_hash = _hash("admin123")
    cur.execute(
        "INSERT OR IGNORE INTO usuarios (usuario, contraseña, rol) VALUES (?,?,?)",
        ("admin", pwd_hash, "admin"),
    )

    # Categorías base
    for cat in ("General", "Electrónica", "Ropa", "Alimentos", "Hogar"):
        cur.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))

    # Métodos de pago base
    for mp in ("Efectivo", "Tarjeta débito", "Tarjeta crédito", "Transferencia"):
        cur.execute("INSERT OR IGNORE INTO metodos_pago (nombre) VALUES (?)", (mp,))

    # Cliente genérico para ventas rápidas
    cur.execute(
        "INSERT OR IGNORE INTO clientes (nombre, identificacion) VALUES (?,?)",
        ("Cliente General", "0000000000"),
    )

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════
#  UTILIDADES INTERNAS
# ══════════════════════════════════════════════════════════════════

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════
#  USUARIOS
# ══════════════════════════════════════════════════════════════════

def autenticar_usuario(usuario: str, contraseña: str):
    """Devuelve el Row del usuario activo si las credenciales son correctas, o None."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND contraseña=? AND activo=1",
            (usuario, _hash(contraseña)),
        ).fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"[DB] autenticar_usuario: {e}")
        return None


def obtener_usuarios():
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, usuario, rol, activo FROM usuarios ORDER BY id"
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_usuarios: {e}")
        return []


def crear_usuario(usuario: str, contraseña: str, rol: str):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO usuarios (usuario, contraseña, rol) VALUES (?,?,?)",
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
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_usuario(uid: int):
    try:
        conn = get_connection()
        conn.execute("UPDATE usuarios SET activo=0 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        return True, "Usuario desactivado."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  CLIENTES
# ══════════════════════════════════════════════════════════════════

def obtener_clientes(filtro: str = ""):
    try:
        conn = get_connection()
        q = f"%{filtro}%"
        rows = conn.execute(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR identificacion LIKE ? ORDER BY nombre",
            (q, q),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_clientes: {e}")
        return []


def crear_cliente(nombre, identificacion="", telefono="", email="", direccion=""):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO clientes (nombre, identificacion, telefono, email, direccion) VALUES (?,?,?,?,?)",
            (nombre, identificacion or None, telefono, email, direccion),
        )
        conn.commit()
        conn.close()
        return True, "Cliente creado."
    except sqlite3.IntegrityError:
        return False, "La identificación ya existe."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_cliente(cid, nombre, identificacion, telefono, email, direccion):
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE clientes SET nombre=?, identificacion=?, telefono=?, email=?, direccion=? WHERE id=?",
            (nombre, identificacion or None, telefono, email, direccion, cid),
        )
        conn.commit()
        conn.close()
        return True, "Cliente actualizado."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_cliente(cid: int):
    try:
        conn = get_connection()
        conn.execute("DELETE FROM clientes WHERE id=?", (cid,))
        conn.commit()
        conn.close()
        return True, "Cliente eliminado."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  CATEGORÍAS
# ══════════════════════════════════════════════════════════════════

def obtener_categorias():
    try:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_categorias: {e}")
        return []


def crear_categoria(nombre, descripcion=""):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO categorias (nombre, descripcion) VALUES (?,?)",
            (nombre, descripcion),
        )
        conn.commit()
        conn.close()
        return True, "Categoría creada."
    except sqlite3.IntegrityError:
        return False, "La categoría ya existe."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  PROVEEDORES
# ══════════════════════════════════════════════════════════════════

def obtener_proveedores(filtro: str = ""):
    try:
        conn = get_connection()
        q = f"%{filtro}%"
        rows = conn.execute(
            "SELECT * FROM proveedores WHERE nombre LIKE ? AND activo=1 ORDER BY nombre",
            (q,),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_proveedores: {e}")
        return []


def crear_proveedor(nombre, contacto="", telefono="", email="", direccion=""):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO proveedores (nombre, contacto, telefono, email, direccion) VALUES (?,?,?,?,?)",
            (nombre, contacto, telefono, email, direccion),
        )
        conn.commit()
        conn.close()
        return True, "Proveedor creado."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_proveedor(pid, nombre, contacto, telefono, email, direccion):
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE proveedores SET nombre=?, contacto=?, telefono=?, email=?, direccion=? WHERE id=?",
            (nombre, contacto, telefono, email, direccion, pid),
        )
        conn.commit()
        conn.close()
        return True, "Proveedor actualizado."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_proveedor(pid: int):
    try:
        conn = get_connection()
        conn.execute("UPDATE proveedores SET activo=0 WHERE id=?", (pid,))
        conn.commit()
        conn.close()
        return True, "Proveedor desactivado."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  MÉTODOS DE PAGO
# ══════════════════════════════════════════════════════════════════

def obtener_metodos_pago():
    try:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM metodos_pago ORDER BY nombre").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_metodos_pago: {e}")
        return []


# ══════════════════════════════════════════════════════════════════
#  PRODUCTOS
# ══════════════════════════════════════════════════════════════════

def obtener_productos(filtro: str = ""):
    try:
        conn = get_connection()
        q = f"%{filtro}%"
        rows = conn.execute(
            """SELECT p.*, c.nombre AS categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON c.id = p.categoria_id
               WHERE p.activo=1 AND (p.nombre LIKE ? OR p.codigo LIKE ?)
               ORDER BY p.nombre""",
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
        row = conn.execute(
            """SELECT p.*, c.nombre AS categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON c.id = p.categoria_id
               WHERE p.id=?""",
            (pid,),
        ).fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"[DB] obtener_producto_por_id: {e}")
        return None


def crear_producto(nombre, precio, cantidad, codigo, marca, detalles, categoria_id=None):
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO productos (nombre, precio, cantidad, codigo, marca, detalles, categoria_id)
               VALUES (?,?,?,?,?,?,?)""",
            (nombre, precio, cantidad, codigo or None, marca, detalles, categoria_id),
        )
        conn.commit()
        conn.close()
        return True, "Producto creado."
    except sqlite3.Error as e:
        return False, str(e)


def actualizar_producto(pid, nombre, precio, cantidad, codigo, marca, detalles, categoria_id=None):
    try:
        conn = get_connection()
        conn.execute(
            """UPDATE productos
               SET nombre=?, precio=?, cantidad=?, codigo=?, marca=?, detalles=?, categoria_id=?
               WHERE id=?""",
            (nombre, precio, cantidad, codigo or None, marca, detalles, categoria_id, pid),
        )
        conn.commit()
        conn.close()
        return True, "Producto actualizado."
    except sqlite3.Error as e:
        return False, str(e)


def eliminar_producto(pid: int):
    """Baja lógica del producto."""
    try:
        conn = get_connection()
        conn.execute("UPDATE productos SET activo=0 WHERE id=?", (pid,))
        conn.commit()
        conn.close()
        return True, "Producto desactivado."
    except sqlite3.Error as e:
        return False, str(e)


def reducir_stock(pid: int, cantidad: int):
    """Descuenta stock directamente (sin pasar por triggers). Uso interno."""
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
        nuevo = conn.execute("SELECT cantidad FROM productos WHERE id=?", (pid,)).fetchone()["cantidad"]
        conn.close()
        return True, nuevo
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  FACTURAS
# ══════════════════════════════════════════════════════════════════

def crear_factura(fecha: str, total: float, cliente: str, items: list,
                  cliente_id: int = None, usuario_id: int = None,
                  metodo_pago_id: int = None, subtotal: float = None,
                  impuesto: float = 0.0):
    """
    items: lista de dicts {producto_id, cantidad, precio_unitario, total}
    Los triggers se encargan de registrar movimientos y actualizar stock.
    """
    subtotal = subtotal if subtotal is not None else total
    try:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO facturas
               (fecha, cliente_id, usuario_id, metodo_pago_id, subtotal, impuesto, total, cliente_nombre)
               VALUES (?,?,?,?,?,?,?,?)""",
            (fecha, cliente_id, usuario_id, metodo_pago_id, subtotal, impuesto, total, cliente),
        )
        factura_id = cur.lastrowid
        for it in items:
            conn.execute(
                """INSERT INTO detalle_factura
                   (factura_id, producto_id, cantidad, precio_unitario, subtotal)
                   VALUES (?,?,?,?,?)""",
                (factura_id, it["producto_id"], it["cantidad"],
                 it["precio_unitario"], it["total"]),
            )
            # El trigger trg_venta_movimiento y trg_salida_stock actualizan stock
        conn.commit()
        conn.close()
        return True, factura_id
    except sqlite3.Error as e:
        return False, str(e)


def obtener_facturas(filtro: str = ""):
    try:
        conn = get_connection()
        q = f"%{filtro}%"
        rows = conn.execute(
            """SELECT f.*, c.nombre AS nombre_cliente, u.usuario AS nombre_usuario,
                      mp.nombre AS nombre_metodo_pago
               FROM facturas f
               LEFT JOIN clientes  c  ON c.id  = f.cliente_id
               LEFT JOIN usuarios  u  ON u.id  = f.usuario_id
               LEFT JOIN metodos_pago mp ON mp.id = f.metodo_pago_id
               WHERE f.cliente_nombre LIKE ? OR CAST(f.id AS TEXT) LIKE ?
               ORDER BY f.id DESC""",
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
            """SELECT df.*, p.nombre
               FROM detalle_factura df
               JOIN productos p ON p.id = df.producto_id
               WHERE df.factura_id=?""",
            (factura_id,),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_detalle_factura: {e}")
        return []


def anular_factura(factura_id: int, usuario_id: int = None):
    """Anula la factura y revierte el stock vía movimientos."""
    try:
        conn = get_connection()
        detalles = conn.execute(
            "SELECT producto_id, cantidad FROM detalle_factura WHERE factura_id=?",
            (factura_id,),
        ).fetchall()
        conn.execute(
            "UPDATE facturas SET estado='anulada' WHERE id=?", (factura_id,)
        )
        for d in detalles:
            conn.execute(
                """INSERT INTO movimientos_inventario
                   (producto_id, usuario_id, tipo, cantidad, referencia, nota)
                   VALUES (?,?,'entrada',?,?,?)""",
                (d["producto_id"], usuario_id, d["cantidad"],
                 f"ANULACION-{factura_id}", "Reversión por anulación de factura"),
            )
        conn.commit()
        conn.close()
        return True, "Factura anulada y stock revertido."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  COMPRAS
# ══════════════════════════════════════════════════════════════════

def crear_compra(proveedor_id: int, usuario_id: int, items: list):
    """
    items: lista de dicts {producto_id, cantidad, precio_unitario}
    El trigger trg_compra_movimiento y trg_entrada_stock actualizan stock.
    """
    total = sum(it["cantidad"] * it["precio_unitario"] for it in items)
    try:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO compras (proveedor_id, usuario_id, total) VALUES (?,?,?)",
            (proveedor_id, usuario_id, total),
        )
        compra_id = cur.lastrowid
        for it in items:
            subtotal = it["cantidad"] * it["precio_unitario"]
            conn.execute(
                """INSERT INTO detalle_compra
                   (compra_id, producto_id, cantidad, precio_unitario, subtotal)
                   VALUES (?,?,?,?,?)""",
                (compra_id, it["producto_id"], it["cantidad"],
                 it["precio_unitario"], subtotal),
            )
            # El trigger trg_compra_movimiento y trg_entrada_stock actualizan stock
        conn.commit()
        conn.close()
        return True, compra_id
    except sqlite3.Error as e:
        return False, str(e)


def obtener_compras(filtro: str = ""):
    try:
        conn = get_connection()
        q = f"%{filtro}%"
        rows = conn.execute(
            """SELECT c.*, p.nombre AS nombre_proveedor, u.usuario AS nombre_usuario
               FROM compras c
               LEFT JOIN proveedores p ON p.id = c.proveedor_id
               LEFT JOIN usuarios    u ON u.id = c.usuario_id
               WHERE (p.nombre LIKE ? OR p.nombre IS NULL) OR CAST(c.id AS TEXT) LIKE ?
               ORDER BY c.id DESC""",
            (q, q),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_compras: {e}")
        return []


def obtener_detalle_compra(compra_id: int):
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT dc.*, p.nombre
               FROM detalle_compra dc
               JOIN productos p ON p.id = dc.producto_id
               WHERE dc.compra_id=?""",
            (compra_id,),
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_detalle_compra: {e}")
        return []


# ══════════════════════════════════════════════════════════════════
#  MOVIMIENTOS DE INVENTARIO
# ══════════════════════════════════════════════════════════════════

def obtener_movimientos(producto_id: int = None, tipo: str = None, limite: int = 100):
    try:
        conn = get_connection()
        query = """
            SELECT m.*, p.nombre AS nombre_producto, u.usuario AS nombre_usuario
            FROM movimientos_inventario m
            JOIN productos p ON p.id = m.producto_id
            LEFT JOIN usuarios u ON u.id = m.usuario_id
            WHERE 1=1
        """
        params = []
        if producto_id:
            query += " AND m.producto_id=?"
            params.append(producto_id)
        if tipo:
            query += " AND m.tipo=?"
            params.append(tipo)
        query += f" ORDER BY m.fecha DESC LIMIT {int(limite)}"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] obtener_movimientos: {e}")
        return []


def registrar_ajuste_inventario(producto_id: int, cantidad: int, nota: str, usuario_id: int = None):
    """Ajuste manual de stock (+cantidad para entrada, -cantidad para salida)."""
    tipo = "entrada" if cantidad > 0 else "salida"
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO movimientos_inventario
               (producto_id, usuario_id, tipo, cantidad, referencia, nota)
               VALUES (?,?,?,?,?,?)""",
            (producto_id, usuario_id, tipo, abs(cantidad), "AJUSTE", nota),
        )
        conn.commit()
        conn.close()
        return True, "Ajuste registrado."
    except sqlite3.Error as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════════

def reporte_resumen():
    """Devuelve métricas generales para el dashboard."""
    try:
        conn = get_connection()
        total_productos = conn.execute("SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]
        total_facturas  = conn.execute("SELECT COUNT(*) FROM facturas WHERE estado='completada'").fetchone()[0]
        bajo_stock      = conn.execute("SELECT COUNT(*) FROM productos WHERE cantidad<=5 AND activo=1").fetchone()[0]
        ventas_mes      = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM facturas WHERE strftime('%Y-%m',fecha)=strftime('%Y-%m','now') AND estado='completada'"
        ).fetchone()[0]
        total_clientes  = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        conn.close()
        return {
            "total_productos": total_productos,
            "total_facturas":  total_facturas,
            "bajo_stock":      bajo_stock,
            "ventas_mes":      ventas_mes,
            "total_clientes":  total_clientes,
        }
    except sqlite3.Error as e:
        print(f"[DB] reporte_resumen: {e}")
        return {}


def reporte_ventas_por_producto():
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT p.nombre,
                      SUM(df.cantidad)  AS unidades,
                      SUM(df.subtotal)  AS ingresos
               FROM detalle_factura df
               JOIN productos p ON p.id = df.producto_id
               JOIN facturas   f ON f.id = df.factura_id
               WHERE f.estado='completada'
               GROUP BY p.id ORDER BY ingresos DESC LIMIT 10"""
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] reporte_ventas_por_producto: {e}")
        return []


def reporte_ventas_por_cliente():
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT COALESCE(c.nombre, f.cliente_nombre) AS cliente,
                      COUNT(f.id) AS facturas,
                      SUM(f.total) AS total_comprado
               FROM facturas f
               LEFT JOIN clientes c ON c.id = f.cliente_id
               WHERE f.estado='completada'
               GROUP BY f.cliente_id ORDER BY total_comprado DESC LIMIT 10"""
        ).fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"[DB] reporte_ventas_por_cliente: {e}")
        return []
    