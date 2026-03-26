# Modulo de facturación buscador, carrito y generación de factura
import tkinter as tk
from tkinter import ttk, messagebox
from utils.helpers import COLORES, formato_moneda

class FacturacionView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORES["fondo"])
        self.ctrl = controller
        self._construir()
        self._actualizar_total()

    # ──────────────── Construcción ────────────────

    def _construir(self):
        # Encabezado
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Gestión de Facturación",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")

        body = tk.Frame(self, bg=COLORES["fondo"])
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._panel_izquierdo(body)
        self._panel_derecho(body)

    def _panel_izquierdo(self, parent):
        """Panel de búsqueda y selección de productos."""
        frm = tk.LabelFrame(parent, text="  Buscar Producto",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=12, pady=10)
        frm.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frm.rowconfigure(2, weight=1)
        frm.columnconfigure(0, weight=1)

        # Buscador
        busq = tk.Frame(frm, bg=COLORES["blanco"])
        busq.grid(row=0, column=0, sticky="ew")
        tk.Label(busq, text="🔍", bg=COLORES["blanco"],
                 font=("Segoe UI", 12)).pack(side="left")
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace_add("write", lambda *a: self._buscar())
        tk.Entry(busq, textvariable=self.var_buscar, font=("Segoe UI", 10),
                 relief="flat", bg=COLORES["fondo"]).pack(
            side="left", fill="x", expand=True, ipady=6, padx=6)

        # Treeview productos
        cols = ("id", "nombre", "precio", "stock")
        self.tv_prod = ttk.Treeview(frm, columns=cols, show="headings",
                                     height=10, selectmode="browse")
        cabeceras = {"id": ("ID", 40), "nombre": ("Nombre", 200),
                     "precio": ("Precio", 90), "stock": ("Stock", 60)}
        for c, (h, w) in cabeceras.items():
            self.tv_prod.heading(c, text=h)
            self.tv_prod.column(c, width=w)
        sb = ttk.Scrollbar(frm, orient="vertical", command=self.tv_prod.yview)
        self.tv_prod.configure(yscrollcommand=sb.set)
        self.tv_prod.grid(row=2, column=0, sticky="nsew", pady=8)
        sb.grid(row=2, column=1, sticky="ns", pady=8)

        # Cantidad + botón agregar
        ctrl_frame = tk.Frame(frm, bg=COLORES["blanco"])
        ctrl_frame.grid(row=3, column=0, sticky="ew")
        tk.Label(ctrl_frame, text="Cantidad:", font=("Segoe UI", 10),
                 bg=COLORES["blanco"]).pack(side="left")
        self.ent_cant = tk.Entry(ctrl_frame, font=("Segoe UI", 10),
                                  relief="flat", bg=COLORES["fondo"], width=8)
        self.ent_cant.insert(0, "1")
        self.ent_cant.pack(side="left", padx=8, ipady=4)
        tk.Button(ctrl_frame, text="➕ Agregar al carrito",
                  font=("Segoe UI", 9, "bold"),
                  bg=COLORES["acento"], fg="white", relief="flat", cursor="hand2",
                  command=self._agregar_item).pack(side="left", ipady=6, padx=4)

        self._buscar()  # carga inicial

    def _panel_derecho(self, parent):
        """Panel de carrito y totales."""
        frm = tk.LabelFrame(parent, text="  Carrito de Factura",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=12, pady=10)
        frm.grid(row=0, column=1, sticky="nsew")
        frm.rowconfigure(2, weight=1)
        frm.columnconfigure(0, weight=1)

        # Cliente
        cli_frame = tk.Frame(frm, bg=COLORES["blanco"])
        cli_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(cli_frame, text="Cliente:", font=("Segoe UI", 10),
                 bg=COLORES["blanco"]).pack(side="left")
        self.ent_cliente = tk.Entry(cli_frame, font=("Segoe UI", 10),
                                    relief="flat", bg=COLORES["fondo"])
        self.ent_cliente.pack(side="left", fill="x", expand=True, ipady=4, padx=8)

        # Tabla carrito
        cols = ("nombre", "cant", "precio", "subtotal")
        self.tv_carrito = ttk.Treeview(frm, columns=cols, show="headings",
                                        height=10, selectmode="browse")
        cabeceras = {"nombre": ("Producto", 180), "cant": ("Cant.", 60),
                     "precio": ("P. Unitario", 100), "subtotal": ("Subtotal", 100)}
        for c, (h, w) in cabeceras.items():
            self.tv_carrito.heading(c, text=h)
            self.tv_carrito.column(c, width=w)
        sb2 = ttk.Scrollbar(frm, orient="vertical", command=self.tv_carrito.yview)
        self.tv_carrito.configure(yscrollcommand=sb2.set)
        self.tv_carrito.grid(row=2, column=0, sticky="nsew", pady=4)
        sb2.grid(row=2, column=1, sticky="ns", pady=4)

        # Total
        total_frame = tk.Frame(frm, bg=COLORES["fondo"], padx=8, pady=8)
        total_frame.grid(row=3, column=0, sticky="ew")
        tk.Label(total_frame, text="TOTAL:",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORES["fondo"], fg=COLORES["texto"]).pack(side="left")
        self.lbl_total = tk.Label(total_frame, text="$0.00",
                                   font=("Segoe UI", 18, "bold"),
                                   bg=COLORES["fondo"], fg=COLORES["exito"])
        self.lbl_total.pack(side="right")

        # Botones
        btn_frame = tk.Frame(frm, bg=COLORES["blanco"])
        btn_frame.grid(row=4, column=0, sticky="ew", pady=8)
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        tk.Button(btn_frame, text="🗑 Quitar",
                  font=("Segoe UI", 9), bg=COLORES["advertencia"], fg="white",
                  relief="flat", cursor="hand2",
                  command=self._quitar_item).grid(row=0, column=0, padx=3,
                                                   sticky="ew", ipady=6)
        tk.Button(btn_frame, text="🔄 Nueva",
                  font=("Segoe UI", 9), bg=COLORES["borde"], fg=COLORES["texto"],
                  relief="flat", cursor="hand2",
                  command=self._nueva_factura).grid(row=0, column=1, padx=3,
                                                     sticky="ew", ipady=6)
        tk.Button(btn_frame, text="✅ Generar Factura",
                  font=("Segoe UI", 9, "bold"), bg=COLORES["exito"], fg="white",
                  relief="flat", cursor="hand2",
                  command=self._generar).grid(row=0, column=2, padx=3,
                                               sticky="ew", ipady=6)

        # Tab historial
        self._construir_historial()

    def _construir_historial(self):
        """Panel extra con el historial de facturas."""
        frm = tk.LabelFrame(self, text="  Historial de Facturas",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=12, pady=8)
        frm.pack(fill="x", padx=16, pady=(0, 12))

        cols = ("id", "fecha", "cliente", "total")
        self.tv_hist = ttk.Treeview(frm, columns=cols, show="headings",
                                     height=4, selectmode="browse")
        for c, h, w in [("id","#",40),("fecha","Fecha",100),
                         ("cliente","Cliente",180),("total","Total",90)]:
            self.tv_hist.heading(c, text=h)
            self.tv_hist.column(c, width=w)
        self.tv_hist.pack(fill="x")
        self.tv_hist.bind("<<TreeviewSelect>>", self._ver_detalle)
        self._cargar_historial()

    # ──────────────── Eventos ────────────────

    def _buscar(self):
        self.tv_prod.delete(*self.tv_prod.get_children())
        for p in self.ctrl.buscar_producto(self.var_buscar.get()):
            self.tv_prod.insert("", "end", iid=str(p["id"]),
                                values=(p["id"], p["nombre"],
                                        formato_moneda(p["precio"]),
                                        p["cantidad"]))

    def _agregar_item(self):
        sel = self.tv_prod.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona un producto.")
            return
        pid   = int(sel[0])
        vals  = self.tv_prod.item(sel[0], "values")
        nombre = vals[1]
        precio = float(vals[2].replace("$", "").replace(",", ""))
        stock  = int(vals[3])
        cant   = self.ent_cant.get()

        ok, msg = self.ctrl.agregar_a_factura(pid, nombre, cant, precio, stock)
        if ok:
            self._refrescar_carrito()
        else:
            messagebox.showerror("Error", msg)

    def _quitar_item(self):
        sel = self.tv_carrito.selection()
        if not sel:
            return
        idx = self.tv_carrito.index(sel[0])
        self.ctrl.quitar_de_factura(idx)
        self._refrescar_carrito()

    def _nueva_factura(self):
        if messagebox.askyesno("Nueva factura", "¿Limpiar el carrito actual?"):
            self.ctrl.nueva_factura()
            self.ent_cliente.delete(0, "end")
            self._refrescar_carrito()

    def _generar(self):
        cliente = self.ent_cliente.get().strip()
        if not cliente:
            messagebox.showwarning("Atención", "Ingresa el nombre del cliente.")
            return
        ok, msg = self.ctrl.generar_factura(cliente)
        if ok:
            messagebox.showinfo("✅ Éxito", msg)
            self.ent_cliente.delete(0, "end")
            self._refrescar_carrito()
            self._cargar_historial()
            self._buscar()  # refrescar stocks
        else:
            messagebox.showerror("Error", msg)

    def _ver_detalle(self, _):
        sel = self.tv_hist.selection()
        if not sel:
            return
        fid = int(sel[0])
        detalles = self.ctrl.detalle_factura(fid)
        if not detalles:
            return
        win = tk.Toplevel(self)
        win.title(f"Factura #{fid}")
        win.configure(bg=COLORES["blanco"])
        win.grab_set()
        tk.Label(win, text=f"Detalle Factura #{fid}",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(padx=20, pady=10)
        cols = ("Producto", "Cantidad", "P. Unitario", "Total")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=len(detalles))
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=140)
        for d in detalles:
            tv.insert("", "end", values=(
                d["nombre"], d["cantidad"],
                formato_moneda(d["precio_unitario"]),
                formato_moneda(d["total"])))
        tv.pack(padx=20, pady=10)
        tk.Button(win, text="Cerrar", command=win.destroy,
                  bg=COLORES["acento"], fg="white", relief="flat",
                  cursor="hand2").pack(pady=8, ipadx=20, ipady=4)

    # ──────────────── Helpers ────────────────

    def _refrescar_carrito(self):
        self.tv_carrito.delete(*self.tv_carrito.get_children())
        for it in self.ctrl.factura_actual.items:
            self.tv_carrito.insert("", "end", values=(
                it.nombre, it.cantidad,
                formato_moneda(it.precio_unitario),
                formato_moneda(it.total)))
        self._actualizar_total()

    def _actualizar_total(self):
        total = self.ctrl.factura_actual.total
        self.lbl_total.configure(text=formato_moneda(total))

    def _cargar_historial(self):
        self.tv_hist.delete(*self.tv_hist.get_children())
        for f in self.ctrl.listar_facturas():
            self.tv_hist.insert("", "end", iid=str(f["id"]),
                                values=(f["id"], f["fecha"],
                                        f["cliente"],
                                        formato_moneda(f["total"])))

