# Modelo de datos Factura y DetalleFactura
from datetime import date

class DetalleFactura:
    def __init__(self, producto_id, nombre, cantidad, precio_unitario):
        self.producto_id     = producto_id
        self.nombre          = nombre
        self.cantidad        = int(cantidad)
        self.precio_unitario = float(precio_unitario)
        self.total           = self.cantidad * self.precio_unitario

    def to_dict(self):
        return {
            "producto_id":     self.producto_id,
            "cantidad":        self.cantidad,
            "precio_unitario": self.precio_unitario,
            "total":           self.total,
        }


class Factura:
    def __init__(self, cliente=""):
        self.id      = None
        self.fecha   = str(date.today())
        self.cliente = cliente
        self.items: list[DetalleFactura] = []

    @property
    def total(self):
        return sum(it.total for it in self.items)

    def agregar_item(self, producto_id, nombre, cantidad, precio_unitario, stock_disponible):
        """Agrega o actualiza un ítem. Valida stock."""
        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a 0."
        # Calcular cuánto ya hay en el carrito
        ya_en_carrito = sum(it.cantidad for it in self.items if it.producto_id == producto_id)
        if ya_en_carrito + cantidad > stock_disponible:
            return False, f"Stock insuficiente. Disponible: {stock_disponible - ya_en_carrito}"
        # Si ya existe el mismo producto, acumula
        for it in self.items:
            if it.producto_id == producto_id:
                it.cantidad += cantidad
                it.total     = it.cantidad * it.precio_unitario
                return True, "Cantidad actualizada."
        self.items.append(DetalleFactura(producto_id, nombre, cantidad, precio_unitario))
        return True, "Producto agregado."

    def quitar_item(self, indice: int):
        if 0 <= indice < len(self.items):
            self.items.pop(indice)

    def limpiar(self):
        self.items.clear()
        self.cliente = ""
        from datetime import date
        self.fecha = str(date.today())

    def validar(self):
        if not self.items:
            return False, "La factura no tiene productos."
        return True, ""

