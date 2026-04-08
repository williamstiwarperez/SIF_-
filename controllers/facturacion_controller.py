# controllers/facturacion_controller.py
# Lógica de negocio para el módulo Facturación
# Versión 2.0 — soporta cliente_id, usuario_id, metodo_pago_id e impuesto

import database as db
from models.factura import Factura


class FacturacionController:

    def __init__(self, usuario_id: int = None):
        self.factura_actual = Factura()
        self.usuario_id = usuario_id          # se pasa desde VentanaPrincipal

    # ── Búsqueda de productos ──────────────────────────────────────────────────

    def buscar_producto(self, termino: str):
        return db.obtener_productos(termino)

    # ── Carrito ────────────────────────────────────────────────────────────────

    def agregar_a_factura(self, producto_id, nombre, cantidad_str, precio_unitario, stock):
        try:
            cantidad = int(cantidad_str)
        except ValueError:
            return False, "Cantidad inválida."
        return self.factura_actual.agregar_item(
            producto_id, nombre, cantidad, precio_unitario, stock
        )

    def quitar_de_factura(self, indice: int):
        self.factura_actual.quitar_item(indice)

    # ── Generación de factura ──────────────────────────────────────────────────

    def generar_factura(self, cliente: str, cliente_id: int = None,
                        metodo_pago_id: int = None, tasa_impuesto: float = 0.0):
        """
        tasa_impuesto: porcentaje decimal, ej. 0.19 para 19 % de IVA.
        """
        self.factura_actual.cliente = cliente
        ok, msg = self.factura_actual.validar()
        if not ok:
            return False, msg

        subtotal = self.factura_actual.total
        impuesto = round(subtotal * tasa_impuesto, 2)
        total    = round(subtotal + impuesto, 2)

        items = [it.to_dict() for it in self.factura_actual.items]

        ok, resultado = db.crear_factura(
            fecha          = self.factura_actual.fecha,
            total          = total,
            cliente        = cliente,
            items          = items,
            cliente_id     = cliente_id,
            usuario_id     = self.usuario_id,
            metodo_pago_id = metodo_pago_id,
            subtotal       = subtotal,
            impuesto       = impuesto,
        )
        if ok:
            self.factura_actual.limpiar()
            return True, f"Factura #{resultado} generada correctamente."
        return False, resultado

    def nueva_factura(self):
        self.factura_actual.limpiar()

    # ── Historial ──────────────────────────────────────────────────────────────

    def listar_facturas(self, filtro=""):
        return db.obtener_facturas(filtro)

    def detalle_factura(self, factura_id):
        return db.obtener_detalle_factura(factura_id)

    def anular_factura(self, factura_id: int):
        return db.anular_factura(factura_id, self.usuario_id)

    # ── Auxiliares ─────────────────────────────────────────────────────────────

    def obtener_clientes(self, filtro=""):
        return db.obtener_clientes(filtro)

    def obtener_metodos_pago(self):
        return db.obtener_metodos_pago()
    
    