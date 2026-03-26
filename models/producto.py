# Modelo de datos Producto
# define la estructura y validaciones basicas
class Producto:
    def __init__(self, id=None, nombre="", precio=0.0, cantidad=0,
                 codigo="", marca="", detalles=""):
        self.id       = id
        self.nombre   = nombre
        self.precio   = precio
        self.cantidad = cantidad
        self.codigo   = codigo
        self.marca    = marca
        self.detalles = detalles

    @classmethod
    def desde_row(cls, row):
        """Construye un Producto desde un sqlite3.Row."""
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            precio=row["precio"],
            cantidad=row["cantidad"],
            codigo=row["codigo"]   or "",
            marca=row["marca"]     or "",
            detalles=row["detalles"] or "",
        )

    def validar(self):
        """Devuelve (True, '') si es válido o (False, 'mensaje') si no lo es."""
        if not self.nombre.strip():
            return False, "El nombre es obligatorio."
        try:
            precio = float(self.precio)
            if precio < 0:
                raise ValueError
        except (ValueError, TypeError):
            return False, "El precio debe ser un número >= 0."
        try:
            cant = int(self.cantidad)
            if cant < 0:
                raise ValueError
        except (ValueError, TypeError):
            return False, "La cantidad debe ser un entero >= 0."
        return True, ""

    def __repr__(self):
        return f"<Producto id={self.id} nombre={self.nombre!r}>"



