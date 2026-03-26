# Funciones de utilidad reutilizables: formateo, colores, etc.

def formato_moneda(valor: float) -> str:
    """Convierte 1250.5 → '$1,250.50'"""
    try:
        return "${:,.2f}".format(float(valor))
    except (ValueError, TypeError):
        return "$0.00"


def color_stock(cantidad: int) -> str:
    """Devuelve color HEX según nivel de stock."""
    if cantidad == 0:
        return "#e74c3c"   # rojo
    if cantidad <= 5:
        return "#e67e22"   # naranja
    return "#27ae60"       # verde


def validar_entero(valor: str, minimo: int = 0) -> tuple[bool, int]:
    try:
        n = int(valor)
        if n < minimo:
            return False, 0
        return True, n
    except (ValueError, TypeError):
        return False, 0


def validar_float(valor: str, minimo: float = 0.0) -> tuple[bool, float]:
    try:
        n = float(valor)
        if n < minimo:
            return False, 0.0
        return True, n
    except (ValueError, TypeError):
        return False, 0.0


# Paleta de colores para toda la UI
COLORES = {
    "primario":    "#1a2a4a",   # azul marino menú
    "secundario":  "#2c3e6b",   # azul menú hover
    "acento":      "#3498db",   # azul botones
    "exito":       "#27ae60",   # verde
    "peligro":     "#e74c3c",   # rojo
    "advertencia": "#e67e22",   # naranja
    "fondo":       "#f0f2f5",   # gris claro fondo
    "blanco":      "#ffffff",
    "texto":       "#2c3e50",
    "texto_claro": "#7f8c8d",
    "borde":       "#dde1e7",
    "cabecera_tv": "#dce8f5",   # Treeview header
}





