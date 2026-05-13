# Panel principal — Dashboard + Reportes esenciales
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
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="Dashboard",
                 font=("Segoe UI", 18, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")
        tk.Label(header, text="Resumen general del sistema",
                 font=("Segoe UI", 10),
                 bg=COLORES["blanco"], fg=COLORES["texto_claro"]).pack(anchor="w")

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
        inner   = self._inner
        resumen = db.reporte_resumen()
        self._tarjetas(inner, resumen)
        self._grafica_stock(inner)
        self._tablas_inferiores(inner)

    def _tarjetas(self, parent, resumen):
        row = tk.Frame(parent, bg=COLORES["fondo"])
        row.pack(fill="x", padx=24, pady=(20, 8))
        datos = [
            ("Ventas del Mes",   formato_moneda(resumen.get("ventas_mes", 0)),  COLORES["exito"]),
            ("Facturas del Mes", str(resumen.get("total_facturas", 0)),          "#8e44ad"),
            ("Total Productos",  str(resumen.get("total_productos", 0)),          COLORES["acento"]),
            ("Bajo Stock",       str(resumen.get("bajo_stock", 0)),              COLORES["advertencia"]),
        ]
        iconos = ["💰", "🧾", "📦", "⚠️"]
        for i, ((titulo, valor, color), icono) in enumerate(zip(datos, iconos)):
            row.columnconfigure(i, weight=1)
            card = tk.Frame(row, bg=COLORES["blanco"], padx=20, pady=16)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            tk.Label(card, text=f"{icono}  {titulo}", font=("Segoe UI", 9),
                     fg=COLORES["texto_claro"], bg=COLORES["blanco"]).pack(anchor="w")
            tk.Label(card, text=valor, font=("Segoe UI", 22, "bold"),
                     fg=color, bg=COLORES["blanco"]).pack(anchor="w")

    def _grafica_stock(self, parent):
        frame = tk.LabelFrame(parent, text="  Stock de Productos (Top 10)",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["texto"],
                              padx=12, pady=12)
        frame.pack(fill="x", padx=24, pady=8)

        productos = db.obtener_productos()[:10]
        if not productos:
            tk.Label(frame, text="Sin productos registrados.",
                     bg=COLORES["blanco"], fg=COLORES["texto_claro"]).pack()
            return

        W, H  = 700, 190
        c     = tk.Canvas(frame, width=W, height=H,
                           bg=COLORES["blanco"], highlightthickness=0)
        c.pack(fill="x")

        max_cant = max(p["cantidad"] for p in productos) or 1
        bar_w    = (W - 60) // len(productos)
        palette  = [COLORES["acento"], COLORES["exito"], "#8e44ad",
                    COLORES["advertencia"], "#16a085", "#c0392b",
                    "#2980b9", "#d35400", "#1abc9c", "#9b59b6"]

        for i, p in enumerate(productos):
            x0    = 40 + i * bar_w + 4
            x1    = x0 + bar_w - 8
            bh    = int((p["cantidad"] / max_cant) * (H - 55))
            y0    = H - 30 - bh
            color = COLORES["peligro"] if p["cantidad"] <= 5 else palette[i % len(palette)]
            c.create_rectangle(x0, y0, x1, H - 30, fill=color, outline="")
            c.create_text((x0 + x1) // 2, y0 - 7,
                          text=str(p["cantidad"]),
                          font=("Segoe UI", 8, "bold"), fill=COLORES["texto"])
            nombre = (p["nombre"][:9] + "…") if len(p["nombre"]) > 10 else p["nombre"]
            c.create_text((x0 + x1) // 2, H - 15,
                          text=nombre, font=("Segoe UI", 7),
                          fill=COLORES["texto_claro"])

        c.create_line(38, 8, 38, H - 28, fill=COLORES["borde"])
        c.create_line(38, H - 28, W - 10, H - 28, fill=COLORES["borde"])

        tk.Label(frame, text="🔴 Barra roja = stock crítico (≤ 5 unidades)",
                 font=("Segoe UI", 8), bg=COLORES["blanco"],
                 fg=COLORES["texto_claro"]).pack(anchor="w", pady=(4, 0))

    def _tablas_inferiores(self, parent):
        row = tk.Frame(parent, bg=COLORES["fondo"])
        row.pack(fill="both", expand=True, padx=24, pady=8)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        self._tabla_top_ventas(row, col=0)
        self._tabla_bajo_stock(row, col=1)

    def _tabla_top_ventas(self, parent, col):
        frame = tk.LabelFrame(parent, text="  Top Productos Más Vendidos",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["texto"],
                              padx=12, pady=8)
        frame.grid(row=0, column=col, padx=(0, 8), sticky="nsew")

        cols = ("pos", "nombre", "unidades", "ingresos")
        tv   = ttk.Treeview(frame, columns=cols, show="headings", height=7)
        for c, h, w, anchor in [
            ("pos",      "#",         35,  "center"),
            ("nombre",   "Producto",  170, "w"),
            ("unidades", "Unidades",   80, "center"),
            ("ingresos", "Ingresos",  100, "e"),
        ]:
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor=anchor)

        for i, r in enumerate(db.reporte_ventas_por_producto(), 1):
            tv.insert("", "end", values=(
                i, r["nombre"], r["unidades"],
                formato_moneda(r["ingresos"])
            ))

        tv.pack(fill="both", expand=True)

    def _tabla_bajo_stock(self, parent, col):
        frame = tk.LabelFrame(parent, text="  ⚠️ Alertas de Stock Bajo",
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORES["blanco"], fg=COLORES["advertencia"],
                              padx=12, pady=8)
        frame.grid(row=0, column=col, padx=(8, 0), sticky="nsew")

        cols = ("nombre", "stock", "precio")
        tv   = ttk.Treeview(frame, columns=cols, show="headings", height=7)
        for c, h, w, anchor in [
            ("nombre", "Producto",  200, "w"),
            ("stock",  "Stock",      70, "center"),
            ("precio", "Precio",    100, "e"),
        ]:
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor=anchor)

        tv.tag_configure("critico", foreground=COLORES["peligro"])
        tv.tag_configure("bajo",    foreground=COLORES["advertencia"])

        productos_bajos = [p for p in db.obtener_productos() if p["cantidad"] <= 5]
        if not productos_bajos:
            tv.insert("", "end", values=("✅ Todo el stock en orden", "", ""))
        else:
            for p in productos_bajos:
                tag = "critico" if p["cantidad"] == 0 else "bajo"
                tv.insert("", "end",
                          values=(p["nombre"], p["cantidad"],
                                  formato_moneda(p["precio"])),
                          tags=(tag,))

        tv.pack(fill="both", expand=True)
