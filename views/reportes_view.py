# Panel de reportes y estadisticas 
import tkinter as tk
from tkinter import ttk
import database as db
from utils.helpers import COLORES, formato_moneda

class ReportesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORES["fondo"])
        self._construir()

    def _construir(self):
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Reportes y Estadísticas",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")

        # Área scrollable
        canvas_scroll = tk.Canvas(self, bg=COLORES["fondo"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas_scroll.pack(fill="both", expand=True)

        inner = tk.Frame(canvas_scroll, bg=COLORES["fondo"])
        win_id = canvas_scroll.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.bind("<Configure>",
                            lambda e: canvas_scroll.itemconfig(win_id, width=e.width))

        self._tarjetas(inner)
        self._grafica_stock(inner)
        self._tabla_top(inner)

    def _tarjetas(self, parent):
        resumen = db.reporte_resumen()
        row = tk.Frame(parent, bg=COLORES["fondo"])
        row.pack(fill="x", padx=24, pady=20)
        datos = [
            ("💰 Ventas del Mes",  formato_moneda(resumen.get("ventas_mes", 0)), COLORES["exito"]),
            ("📦 Total Productos", str(resumen.get("total_productos", 0)),        COLORES["acento"]),
            ("🧾 Total Facturas",  str(resumen.get("total_facturas", 0)),         "#8e44ad"),
            ("⚠️ Bajo Stock",      str(resumen.get("bajo_stock", 0)),             COLORES["advertencia"]),
        ]
        for i, (t, v, c) in enumerate(datos):
            row.columnconfigure(i, weight=1)
            card = tk.Frame(row, bg=COLORES["blanco"], padx=20, pady=14)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            tk.Label(card, text=t, font=("Segoe UI", 9),
                     fg=COLORES["texto_claro"], bg=COLORES["blanco"]).pack(anchor="w")
            tk.Label(card, text=v, font=("Segoe UI", 20, "bold"),
                     fg=c, bg=COLORES["blanco"]).pack(anchor="w")

    def _grafica_stock(self, parent):
        """Gráfica de barras del inventario por producto (Canvas nativo)."""
        frame = tk.LabelFrame(parent, text="  Stock de Productos (Top 10)",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["texto"],
                              padx=12, pady=12)
        frame.pack(fill="x", padx=24, pady=8)

        productos = db.obtener_productos()[:10]
        if not productos:
            tk.Label(frame, text="Sin datos", bg=COLORES["blanco"]).pack()
            return

        W, H = 700, 220
        canvas = tk.Canvas(frame, width=W, height=H,
                           bg=COLORES["blanco"], highlightthickness=0)
        canvas.pack()

        max_cant = max(p["cantidad"] for p in productos) or 1
        bar_w = (W - 60) // len(productos)
        colors = [COLORES["acento"], COLORES["exito"], "#8e44ad", COLORES["advertencia"],
                  "#16a085", "#c0392b", "#2980b9", "#d35400", "#1abc9c", "#9b59b6"]

        for i, p in enumerate(productos):
            x0 = 40 + i * bar_w + 4
            bh = int((p["cantidad"] / max_cant) * (H - 60))
            y0 = H - 30 - bh
            x1 = x0 + bar_w - 8
            color = colors[i % len(colors)]
            canvas.create_rectangle(x0, y0, x1, H - 30, fill=color, outline="")
            # valor encima
            canvas.create_text((x0+x1)//2, y0 - 6, text=str(p["cantidad"]),
                               font=("Segoe UI", 8), fill=COLORES["texto"])
            # etiqueta
            nombre = p["nombre"][:8] + ".." if len(p["nombre"]) > 10 else p["nombre"]
            canvas.create_text((x0+x1)//2, H - 16, text=nombre,
                               font=("Segoe UI", 7), fill=COLORES["texto_claro"],
                               angle=0)
        # eje y
        canvas.create_line(38, 10, 38, H - 28, fill=COLORES["borde"])
        canvas.create_line(38, H - 28, W - 10, H - 28, fill=COLORES["borde"])

    def _tabla_top(self, parent):
        frame = tk.LabelFrame(parent, text="  Productos Más Vendidos",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["texto"],
                              padx=12, pady=8)
        frame.pack(fill="x", padx=24, pady=8)

        cols = ("pos", "nombre", "unidades", "ingresos")
        tv = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        for c, h, w in [("pos","#",40),("nombre","Producto",220),
                         ("unidades","Unidades Vendidas",140),
                         ("ingresos","Ingresos Generados",140)]:
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor="center")
        tv.column("nombre", anchor="w")
        for i, row in enumerate(db.reporte_ventas_por_producto(), 1):
            tv.insert("", "end", values=(i, row["nombre"], row["unidades"],
                                          formato_moneda(row["ingresos"])))
        tv.pack(fill="x")
