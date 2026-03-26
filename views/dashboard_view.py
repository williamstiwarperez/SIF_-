# Panel de inicio con metricas y tablas recientes
import tkinter as tk
from tkinter import ttk
import database as db
from utils.helpers import COLORES, formato_moneda

class DashboardView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORES["fondo"])
        self.app = app
        self._construir()

    def _construir(self):
        # Encabezado
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="Dashboard", font=("Segoe UI", 18, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")
        tk.Label(header, text="Bienvenido al Sistema de Inventario y Facturación",
                 font=("Segoe UI", 10), bg=COLORES["blanco"],
                 fg=COLORES["texto_claro"]).pack(anchor="w")

        # Área scrollable
        canvas = tk.Canvas(self, bg=COLORES["fondo"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLORES["fondo"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        self._inner = inner
        self._cargar_datos()

    def _cargar_datos(self):
        inner = self._inner
        resumen = db.reporte_resumen()

        # ── Tarjetas de métricas ──
        cards_frame = tk.Frame(inner, bg=COLORES["fondo"])
        cards_frame.pack(fill="x", padx=24, pady=20)

        tarjetas = [
            ("📦 Total Productos",  str(resumen.get("total_productos", 0)),  COLORES["acento"]),
            ("🧾 Facturas del Mes", str(resumen.get("total_facturas", 0)),   "#8e44ad"),
            ("⚠️ Bajo Stock",       str(resumen.get("bajo_stock", 0)),       COLORES["advertencia"]),
            ("💰 Ventas del Mes",   formato_moneda(resumen.get("ventas_mes", 0)), COLORES["exito"]),
        ]
        for i, (titulo, valor, color) in enumerate(tarjetas):
            cards_frame.columnconfigure(i, weight=1)
            card = tk.Frame(cards_frame, bg=COLORES["blanco"],
                            padx=20, pady=16, relief="flat")
            card.grid(row=0, column=i, padx=8, sticky="ew")
            tk.Label(card, text=titulo, font=("Segoe UI", 9),
                     fg=COLORES["texto_claro"], bg=COLORES["blanco"]).pack(anchor="w")
            tk.Label(card, text=valor, font=("Segoe UI", 22, "bold"),
                     fg=color, bg=COLORES["blanco"]).pack(anchor="w")

        # ── Tablas ──
        tablas_frame = tk.Frame(inner, bg=COLORES["fondo"])
        tablas_frame.pack(fill="both", expand=True, padx=24, pady=4)
        tablas_frame.columnconfigure(0, weight=1)
        tablas_frame.columnconfigure(1, weight=1)

        # Productos recientes
        self._tabla_recientes(tablas_frame, 0)
        # Top ventas
        self._tabla_top_ventas(tablas_frame, 1)

    def _tabla_recientes(self, parent, col):
        frame = tk.LabelFrame(parent, text="  Productos Recientes",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["texto"],
                              padx=12, pady=8)
        frame.grid(row=0, column=col, padx=8, sticky="nsew")

        cols = ("ID", "Nombre", "Stock", "Precio")
        tv = ttk.Treeview(frame, columns=cols, show="headings", height=7)
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=80)
        tv.column("Nombre", width=150)

        productos = db.obtener_productos()[:8]
        for p in productos:
            tv.insert("", "end", values=(p["id"], p["nombre"],
                                          p["cantidad"],
                                          formato_moneda(p["precio"])))
        tv.pack(fill="both", expand=True)

    def _tabla_top_ventas(self, parent, col):
        frame = tk.LabelFrame(parent, text="  Top Ventas",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["texto"],
                              padx=12, pady=8)
        frame.grid(row=0, column=col, padx=8, sticky="nsew")

        cols = ("Producto", "Unidades", "Ingresos")
        tv = ttk.Treeview(frame, columns=cols, show="headings", height=7)
        for c in cols:
            tv.heading(c, text=c)
        tv.column("Producto", width=180)
        tv.column("Unidades", width=80)
        tv.column("Ingresos", width=100)

        for row in db.reporte_ventas_por_producto():
            tv.insert("", "end", values=(row["nombre"], row["unidades"],
                                          formato_moneda(row["ingresos"])))
        tv.pack(fill="both", expand=True)



