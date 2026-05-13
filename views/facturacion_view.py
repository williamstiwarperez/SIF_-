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

    def _construir(self):
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
        frm = tk.LabelFrame(parent, text="  Buscar Producto",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=12, pady=10)
        frm.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frm.rowconfigure(2, weight=1)
        frm.columnconfigure(0, weight=1)

        busq = tk.Frame(frm, bg=COLORES["blanco"])
        busq.grid(row=0, column=0, sticky="ew")
        tk.Label(busq, text="🔍", bg=COLORES["blanco"],
                 font=("Segoe UI", 12)).pack(side="left")
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace_add("write", lambda *a: self._buscar())
        tk.Entry(busq, textvariable=self.var_buscar, font=("Segoe UI", 10),
                 relief="flat", bg=COLORES["fondo"]).pack(
            side="left", fill="x", expand=True, ipady=6, padx=6)

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

        self._buscar()

    def _panel_derecho(self, parent):
        frm = tk.LabelFrame(parent, text="  Carrito de Factura",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=12, pady=10)
        frm.grid(row=0, column=1, sticky="nsew")
        frm.rowconfigure(2, weight=1)
        frm.columnconfigure(0, weight=1)

        # ── Buscador de clientes con autocompletado ──────────────────────────
        self._cliente_id      = None       # ID del cliente seleccionado
        self._popup_clientes  = None       # Toplevel del dropdown
        self._lb_clientes     = None       # Listbox dentro del popup
        self._clientes_data   = []         # [(id, nombre, identificacion), …]
        self._seleccionando   = False      # guarda para no re-abrir popup al set()

        cli_frame = tk.Frame(frm, bg=COLORES["blanco"])
        cli_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        cli_frame.columnconfigure(1, weight=1)

        tk.Label(cli_frame, text="Cliente:", font=("Segoe UI", 10),
                 bg=COLORES["blanco"]).grid(row=0, column=0, sticky="w")

        self.var_cliente_busq = tk.StringVar()
        self.var_cliente_busq.trace_add("write", lambda *_: self._buscar_cliente_dropdown())
        self.ent_cliente = tk.Entry(cli_frame, textvariable=self.var_cliente_busq,
                                    font=("Segoe UI", 10), relief="flat",
                                    bg=COLORES["fondo"])
        self.ent_cliente.grid(row=0, column=1, sticky="ew", ipady=4, padx=8)

        # Etiqueta de confirmación del cliente vinculado
        self.lbl_cli_ok = tk.Label(cli_frame, text="", font=("Segoe UI", 8),
                                    bg=COLORES["blanco"], fg=COLORES["exito"])
        self.lbl_cli_ok.grid(row=1, column=1, sticky="w", padx=8, pady=(0, 6))

        self.ent_cliente.bind("<FocusOut>",
                              lambda e: self.after(200, self._ocultar_popup_clientes))
        self.ent_cliente.bind("<Escape>",   lambda e: self._ocultar_popup_clientes())
        self.ent_cliente.bind("<Down>",     lambda e: self._popup_focus())
        self.ent_cliente.bind("<Return>",   lambda e: self._popup_focus())

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

        total_frame = tk.Frame(frm, bg=COLORES["fondo"], padx=8, pady=8)
        total_frame.grid(row=3, column=0, sticky="ew")
        tk.Label(total_frame, text="TOTAL:",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORES["fondo"], fg=COLORES["texto"]).pack(side="left")
        self.lbl_total = tk.Label(total_frame, text="$0.00",
                                   font=("Segoe UI", 18, "bold"),
                                   bg=COLORES["fondo"], fg=COLORES["exito"])
        self.lbl_total.pack(side="right")

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

        self._construir_historial()

    def _construir_historial(self):
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
        pid    = int(sel[0])
        vals   = self.tv_prod.item(sel[0], "values")
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
            self._seleccionando = True
            self.var_cliente_busq.set("")
            self._seleccionando = False
            self._cliente_id = None
            self.lbl_cli_ok.configure(text="")
            self._refrescar_carrito()

    def _generar(self):
        cliente = self.var_cliente_busq.get().strip()
        if not cliente:
            messagebox.showwarning("Atención", "Ingresa o busca el nombre del cliente.")
            return
        ok, msg = self.ctrl.generar_factura(cliente, cliente_id=self._cliente_id)
        if ok:
            messagebox.showinfo("✅ Éxito", msg)
            self._seleccionando = True
            self.var_cliente_busq.set("")
            self._seleccionando = False
            self._cliente_id = None
            self.lbl_cli_ok.configure(text="")
            self._refrescar_carrito()
            self._cargar_historial()
            self._buscar()
        else:
            messagebox.showerror("Error", msg)

    # ──────────────── Buscador de clientes ────────────────

    def _buscar_cliente_dropdown(self):
        """Dispara la búsqueda cada vez que cambia el texto del campo cliente."""
        if self._seleccionando:
            return
        # El usuario escribió manualmente → desvincula cualquier cliente previo
        self._cliente_id = None
        self.lbl_cli_ok.configure(text="")

        texto = self.var_cliente_busq.get().strip()
        if len(texto) < 1:
            self._ocultar_popup_clientes()
            return

        resultados = self.ctrl.obtener_clientes(texto)
        if not resultados:
            self._ocultar_popup_clientes()
            return

        self._clientes_data = [
            (r["id"], r["nombre"], r["identificacion"] or "")
            for r in resultados
        ]
        self._mostrar_popup_clientes()

    def _mostrar_popup_clientes(self):
        """Crea o actualiza el Toplevel dropdown con los resultados."""
        if self._popup_clientes is None or not self._popup_clientes.winfo_exists():
            self._popup_clientes = tk.Toplevel(self)
            self._popup_clientes.overrideredirect(True)
            self._popup_clientes.attributes("-topmost", True)

            borde = tk.Frame(self._popup_clientes,
                             bg=COLORES["acento"], bd=0)
            borde.pack(fill="both", expand=True, padx=1, pady=1)

            inner = tk.Frame(borde, bg=COLORES["blanco"])
            inner.pack(fill="both", expand=True)

            sb = tk.Scrollbar(inner, orient="vertical")
            sb.pack(side="right", fill="y")

            self._lb_clientes = tk.Listbox(
                inner,
                font=("Segoe UI", 9),
                relief="flat", bd=0,
                bg=COLORES["blanco"], fg=COLORES["texto"],
                selectbackground=COLORES["acento"],
                selectforeground="white",
                activestyle="none",
                yscrollcommand=sb.set,
            )
            self._lb_clientes.pack(fill="both", expand=True)
            sb.config(command=self._lb_clientes.yview)

            self._lb_clientes.bind("<<ListboxSelect>>", self._seleccionar_cliente)
            self._lb_clientes.bind("<Return>",          self._seleccionar_cliente)
            self._lb_clientes.bind("<Escape>",
                                   lambda e: self._ocultar_popup_clientes())
            self._lb_clientes.bind("<FocusOut>",
                                   lambda e: self.after(200,
                                       self._ocultar_popup_clientes))

        # Rellenar la lista
        self._lb_clientes.delete(0, "end")
        for cid, nombre, ident in self._clientes_data:
            sufijo = f"  —  ID doc: {ident}" if ident else f"  —  #DB: {cid}"
            self._lb_clientes.insert("end", f"{nombre}{sufijo}")

        # Altura dinámica: máximo 6 ítems visibles
        n = min(6, len(self._clientes_data))
        self._lb_clientes.configure(height=n)

        # Posicionar justo debajo del Entry
        self.ent_cliente.update_idletasks()
        x = self.ent_cliente.winfo_rootx()
        y = self.ent_cliente.winfo_rooty() + self.ent_cliente.winfo_height()
        w = self.ent_cliente.winfo_width()
        h = n * 22 + 4
        self._popup_clientes.geometry(f"{w}x{h}+{x}+{y}")
        self._popup_clientes.deiconify()

    def _ocultar_popup_clientes(self):
        if self._popup_clientes and self._popup_clientes.winfo_exists():
            self._popup_clientes.withdraw()

    def _popup_focus(self):
        """Mueve el foco al Listbox cuando el usuario presiona ↓ o Enter."""
        if self._lb_clientes and self._lb_clientes.winfo_exists():
            self._lb_clientes.focus_set()
            if self._lb_clientes.size() > 0:
                self._lb_clientes.selection_set(0)
                self._lb_clientes.activate(0)

    def _seleccionar_cliente(self, event=None):
        """Vincula el cliente elegido en el Listbox al campo de factura."""
        if self._lb_clientes is None:
            return
        sel = self._lb_clientes.curselection()
        if not sel:
            return
        idx = sel[0]
        cid, nombre, ident = self._clientes_data[idx]
        self._cliente_id = cid
        # Escribir nombre sin disparar nueva búsqueda
        self._seleccionando = True
        self.var_cliente_busq.set(nombre)
        self._seleccionando = False
        # Confirmación visual
        etq = f"✓  Vinculado  |  ID doc: {ident}" if ident else f"✓  Vinculado  |  #DB: {cid}"
        self.lbl_cli_ok.configure(text=etq)
        self._ocultar_popup_clientes()
        self.ent_cliente.focus_set()
        self.ent_cliente.icursor("end")

    def _ver_detalle(self, _):
        sel = self.tv_hist.selection()
        if not sel:
            return
        fid = int(sel[0])
        detalles = self.ctrl.detalle_factura(fid)
        if not detalles:
            return

        factura_row = None
        for f in self.ctrl.listar_facturas():
            if f["id"] == fid:
                factura_row = f
                break

        self._mostrar_factura_profesional(fid, detalles, factura_row)

    def _mostrar_factura_profesional(self, fid, detalles, factura_row):
        win = tk.Toplevel(self)
        win.title(f"Factura #{fid:04d}")
        win.geometry("680x700")
        win.configure(bg="#f5f6fa")
        win.grab_set()
        win.resizable(False, False)

        canvas = tk.Canvas(win, bg="#f5f6fa", highlightthickness=0)
        vsb = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        contenedor = tk.Frame(canvas, bg="#f5f6fa")
        window_id = canvas.create_window((0, 0), window=contenedor, anchor="nw", width=660)

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        contenedor.bind("<Configure>", _on_configure)

        # ── Hoja blanca ──
        hoja = tk.Frame(contenedor, bg="white",
                        highlightbackground="#dde1e7", highlightthickness=1)
        hoja.pack(padx=24, pady=24, fill="both", expand=True)

        # ENCABEZADO
        enc = tk.Frame(hoja, bg=COLORES["primario"])
        enc.pack(fill="x")

        izq = tk.Frame(enc, bg=COLORES["primario"])
        izq.pack(side="left", padx=28, pady=20)
        tk.Label(izq, text="SIF", font=("Segoe UI", 26, "bold"),
                 bg=COLORES["primario"], fg="white").pack(anchor="w")
        tk.Label(izq, text="Sistema de Inventario y Facturación",
                 font=("Segoe UI", 9), bg=COLORES["primario"],
                 fg="#a0c4e8").pack(anchor="w")

        der = tk.Frame(enc, bg=COLORES["primario"])
        der.pack(side="right", padx=28, pady=20)
        tk.Label(der, text="FACTURA", font=("Segoe UI", 11, "bold"),
                 bg=COLORES["primario"], fg="#a0c4e8").pack(anchor="e")
        tk.Label(der, text=f"N°  {fid:04d}", font=("Segoe UI", 22, "bold"),
                 bg=COLORES["primario"], fg="white").pack(anchor="e")

        # DATOS CLIENTE / FECHA
        datos = tk.Frame(hoja, bg="white")
        datos.pack(fill="x", padx=28, pady=(20, 0))

        col_emp = tk.Frame(datos, bg="white")
        col_emp.pack(side="left", fill="x", expand=True)
        tk.Label(col_emp, text="EMITIDO POR", font=("Segoe UI", 7, "bold"),
                 bg="white", fg=COLORES["texto_claro"]).pack(anchor="w")
        tk.Label(col_emp, text="SIF — Sistema Integrado de Facturación",
                 font=("Segoe UI", 9), bg="white", fg=COLORES["texto"]).pack(anchor="w")
        tk.Label(col_emp, text="NIT: 000-000-000-0",
                 font=("Segoe UI", 9), bg="white", fg=COLORES["texto_claro"]).pack(anchor="w")

        col_cli = tk.Frame(datos, bg="white")
        col_cli.pack(side="right")

        cliente_nombre = factura_row["cliente_nombre"] if factura_row else "—"
        fecha_val = factura_row["fecha"][:10] if factura_row else "—"

        def _fila_dato(parent, etiqueta, valor):
            f = tk.Frame(parent, bg="white")
            f.pack(fill="x", pady=1)
            tk.Label(f, text=etiqueta, font=("Segoe UI", 8, "bold"),
                     bg="white", fg=COLORES["texto_claro"],
                     width=10, anchor="e").pack(side="left", padx=(0, 6))
            tk.Label(f, text=valor, font=("Segoe UI", 9),
                     bg="white", fg=COLORES["texto"]).pack(side="left")

        _fila_dato(col_cli, "CLIENTE:", cliente_nombre)
        _fila_dato(col_cli, "FECHA:", fecha_val)
        _fila_dato(col_cli, "FACTURA N°:", f"{fid:04d}")

        # SEPARADOR
        tk.Frame(hoja, bg=COLORES["acento"], height=2).pack(fill="x", padx=28, pady=14)

        # TABLA PRODUCTOS
        tbl_frame = tk.Frame(hoja, bg="white")
        tbl_frame.pack(fill="x", padx=28)

        cab = tk.Frame(tbl_frame, bg=COLORES["primario"])
        cab.pack(fill="x")
        for texto, ancho, alinea in [
            ("#", 4, "center"),
            ("DESCRIPCIÓN DEL PRODUCTO", 30, "w"),
            ("CANT.", 6, "center"),
            ("P. UNIT.", 10, "e"),
            ("SUBTOTAL", 10, "e"),
        ]:
            tk.Label(cab, text=texto, font=("Segoe UI", 8, "bold"),
                     bg=COLORES["primario"], fg="white",
                     width=ancho, anchor=alinea,
                     padx=6, pady=6).pack(side="left")

        for i, d in enumerate(detalles):
            fila_bg = "white" if i % 2 == 0 else "#f8f9fb"
            fila = tk.Frame(tbl_frame, bg=fila_bg,
                            highlightbackground="#eaeaea", highlightthickness=1)
            fila.pack(fill="x")
            precio = d["precio_unitario"]
            subtotal_item = d["subtotal"] if "subtotal" in d.keys() else precio * d["cantidad"]
            for texto, ancho, alinea in [
                (str(i + 1), 4, "center"),
                (d["nombre"], 30, "w"),
                (str(d["cantidad"]), 6, "center"),
                (formato_moneda(precio), 10, "e"),
                (formato_moneda(subtotal_item), 10, "e"),
            ]:
                tk.Label(fila, text=texto, font=("Segoe UI", 9),
                         bg=fila_bg, fg=COLORES["texto"],
                         width=ancho, anchor=alinea,
                         padx=6, pady=5).pack(side="left")

        # TOTALES
        tot_outer = tk.Frame(hoja, bg="white")
        tot_outer.pack(fill="x", padx=28, pady=(10, 0))
        tot_frame = tk.Frame(tot_outer, bg="white")
        tot_frame.pack(side="right")

        subtotal_val = factura_row["subtotal"] if factura_row and "subtotal" in factura_row.keys() else None
        impuesto_val = factura_row["impuesto"] if factura_row and "impuesto" in factura_row.keys() else None
        total_val    = (factura_row["total"] if factura_row and "total" in factura_row.keys()
                        else sum(d["precio_unitario"] * d["cantidad"] for d in detalles))

        def _fila_total(etiqueta, valor):
            f = tk.Frame(tot_frame, bg="white")
            f.pack(fill="x", pady=1)
            tk.Label(f, text=etiqueta, font=("Segoe UI", 9),
                     bg="white", fg=COLORES["texto_claro"],
                     width=16, anchor="e").pack(side="left", padx=(0, 12))
            tk.Label(f, text=valor, font=("Segoe UI", 9),
                     bg="white", fg=COLORES["texto"],
                     width=12, anchor="e").pack(side="left")

        tk.Frame(tot_frame, bg=COLORES["borde"], height=1).pack(fill="x", pady=4)

        if subtotal_val is not None:
            _fila_total("Subtotal:", formato_moneda(subtotal_val))
        if impuesto_val is not None:
            _fila_total("IVA / Impuesto:", formato_moneda(impuesto_val))

        total_frm = tk.Frame(tot_frame, bg=COLORES["primario"], padx=10, pady=6)
        total_frm.pack(fill="x", pady=(6, 0))
        tk.Label(total_frm, text="TOTAL A PAGAR:", font=("Segoe UI", 10, "bold"),
                 bg=COLORES["primario"], fg="#a0c4e8").pack(side="left", padx=(0, 20))
        tk.Label(total_frm, text=formato_moneda(total_val), font=("Segoe UI", 14, "bold"),
                 bg=COLORES["primario"], fg="white").pack(side="right")

        # PIE
        tk.Frame(hoja, bg=COLORES["borde"], height=1).pack(fill="x", padx=28, pady=(18, 0))
        pie = tk.Frame(hoja, bg="white")
        pie.pack(fill="x", padx=28, pady=(8, 20))
        tk.Label(pie, text="Gracias por su compra  •  Documento válido como comprobante de pago.",
                 font=("Segoe UI", 8), bg="white", fg=COLORES["texto_claro"]).pack(side="left")
        tk.Label(pie, text="SIF v2.0", font=("Segoe UI", 8),
                 bg="white", fg=COLORES["texto_claro"]).pack(side="right")

        # BOTÓN CERRAR
        btn_frame = tk.Frame(contenedor, bg="#f5f6fa")
        btn_frame.pack(pady=(0, 20))
        tk.Button(btn_frame, text="✕  Cerrar", font=("Segoe UI", 9, "bold"),
                  bg=COLORES["acento"], fg="white", relief="flat", cursor="hand2",
                  command=win.destroy).pack(ipadx=24, ipady=6)

        win.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

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
        self.lbl_total.configure(text=formato_moneda(self.ctrl.factura_actual.total))

    def _cargar_historial(self):
        self.tv_hist.delete(*self.tv_hist.get_children())
        for f in self.ctrl.listar_facturas():
            self.tv_hist.insert("", "end", iid=str(f["id"]),
                                values=(f["id"], f["fecha"],
                                        f["cliente_nombre"],
                                        formato_moneda(f["total"])))