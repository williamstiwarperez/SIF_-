# Logica de negocio para el módulo Inventario
# Une la vista con la base de datos

import database as db
from models.producto import Producto

class InventarioController:

    def listar(self, filtro: str = "") -> list[Producto]:
        rows = db.obtener_productos(filtro)
        return [Producto.desde_row(r) for r in rows]

    def agregar(self, nombre, precio, cantidad, codigo, marca, detalles):
        p = Producto(nombre=nombre, precio=precio, cantidad=cantidad,
                     codigo=codigo, marca=marca, detalles=detalles)
        ok, msg = p.validar()
        if not ok:
            return False, msg
        return db.crear_producto(nombre, float(precio), int(cantidad), codigo, marca, detalles)

    def editar(self, pid, nombre, precio, cantidad, codigo, marca, detalles):
        p = Producto(id=pid, nombre=nombre, precio=precio, cantidad=cantidad,
                     codigo=codigo, marca=marca, detalles=detalles)
        ok, msg = p.validar()
        if not ok:
            return False, msg
        return db.actualizar_producto(pid, nombre, float(precio), int(cantidad), codigo, marca, detalles)

    def eliminar(self, pid: int):
        return db.eliminar_producto(pid)

    def obtener_por_id(self, pid: int):
        row = db.obtener_producto_por_id(pid)
        return Producto.desde_row(row) if row else None
