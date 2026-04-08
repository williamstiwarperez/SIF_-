# controllers/inventario_controller.py
# Lógica de negocio para el módulo Inventario
# Versión 2.0 — soporta categoría, baja lógica y ajustes de stock

import database as db
from models.producto import Producto


class InventarioController:

    def __init__(self, usuario_id: int = None):
        self.usuario_id = usuario_id

    # ── CRUD productos ─────────────────────────────────────────────────────────

    def listar(self, filtro: str = "") -> list[Producto]:
        rows = db.obtener_productos(filtro)
        return [Producto.desde_row(r) for r in rows]

    def agregar(self, nombre, precio, cantidad, codigo, marca, detalles, categoria_id=None):
        p = Producto(nombre=nombre, precio=precio, cantidad=cantidad,
                     codigo=codigo, marca=marca, detalles=detalles)
        ok, msg = p.validar()
        if not ok:
            return False, msg
        return db.crear_producto(
            nombre, float(precio), int(cantidad), codigo, marca, detalles, categoria_id
        )

    def editar(self, pid, nombre, precio, cantidad, codigo, marca, detalles, categoria_id=None):
        p = Producto(id=pid, nombre=nombre, precio=precio, cantidad=cantidad,
                     codigo=codigo, marca=marca, detalles=detalles)
        ok, msg = p.validar()
        if not ok:
            return False, msg
        return db.actualizar_producto(
            pid, nombre, float(precio), int(cantidad), codigo, marca, detalles, categoria_id
        )

    def eliminar(self, pid: int):
        """Baja lógica (activo=0)."""
        return db.eliminar_producto(pid)

    def obtener_por_id(self, pid: int):
        row = db.obtener_producto_por_id(pid)
        return Producto.desde_row(row) if row else None

    # ── Categorías ─────────────────────────────────────────────────────────────

    def listar_categorias(self):
        return db.obtener_categorias()

    def crear_categoria(self, nombre, descripcion=""):
        return db.crear_categoria(nombre, descripcion)

    # ── Movimientos ────────────────────────────────────────────────────────────

    def ajustar_stock(self, producto_id: int, cantidad: int, nota: str):
        """cantidad positiva = entrada, negativa = salida."""
        return db.registrar_ajuste_inventario(
            producto_id, cantidad, nota, self.usuario_id
        )

    def historial_movimientos(self, producto_id: int = None, tipo: str = None):
        return db.obtener_movimientos(producto_id, tipo)
    
    
    
    
    