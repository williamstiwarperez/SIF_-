# Logica de negocio para el modulo Facturacion

import database as db
from models.factura import Factura

class FacturacionController:

    def __init__(self):
        self.factura_actual = Factura()

    def buscar_producto(self, termino: str):
        return db.obtener_productos(termino)

    def agregar_a_factura(self, producto_id, nombre, cantidad_str, precio_unitario, stock):
        try:
            cantidad = int(cantidad_str)
        except ValueError:
            return False, "Cantidad inválida."
        return self.factura_actual.agregar_item(producto_id, nombre, cantidad, precio_unitario, stock)

    def quitar_de_factura(self, indice: int):
        self.factura_actual.quitar_item(indice)

    def generar_factura(self, cliente: str):
        self.factura_actual.cliente = cliente
        ok, msg = self.factura_actual.validar()
        if not ok:
            return False, msg
        items = [it.to_dict() for it in self.factura_actual.items]
        ok, resultado = db.crear_factura(
            self.factura_actual.fecha,
            self.factura_actual.total,
            cliente,
            items,
        )
        if ok:
            self.factura_actual.limpiar()
            return True, f"Factura #{resultado} generada correctamente."
        return False, resultado

    def nueva_factura(self):
        self.factura_actual.limpiar()

    def listar_facturas(self, filtro=""):
        return db.obtener_facturas(filtro)

    def detalle_factura(self, factura_id):
        return db.obtener_detalle_factura(factura_id)






