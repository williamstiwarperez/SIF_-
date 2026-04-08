# CRUD completo de productos
import tkinter as tk
from tkinter import ttk, messagebox
from utils.helpers import COLORES, formato_moneda, color_stock

class InventarioView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORES["fondo"])
        self.ctrl = controller
        self._id_seleccionado = None
        self._construir()
        self._cargar_tabla()

    # ──────────────── Construcción UI ────────────────

    def _construir(self):
        # Encabezado
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Gestión de Inventario",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")

        # Cuerpo dividido: formulario izq | tabla der
        body = tk.Frame(self, bg=COLORES["fondo"])
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._construir_formulario(body)
        self._construir_tabla(body)

    def _construir_formulario(self, parent):
        frm = tk.LabelFrame(parent, text="  Datos del Producto",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=16, pady=12)
        frm.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        frm.configure(width=260)

        campos = [
            ("Nombre *",   "nombre"),
            ("Código",     "codigo"),
            ("Marca",      "marca"),
            ("Precio *",   "precio"),
            ("Cantidad *", "cantidad"),
            ("Detalles",   "detalles"),
        ]
        self._entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(frm, text=label, font=("Segoe UI", 9),
                     fg=COLORES["texto_claro"], bg=COLORES["blanco"],
                     anchor="w").grid(row=i*2, column=0, sticky="w", pady=(6, 0))
            if key == "detalles":
                ent = tk.Text(frm, font=("Segoe UI", 10), height=3,
                              relief="flat", bg=COLORES["fondo"])
            else:
                ent = tk.Entry(frm, font=("Segoe UI", 10),
                               relief="flat", bg=COLORES["fondo"])
            ent.grid(row=i*2+1, column=0, sticky="ew", ipady=5, pady=1)
            self._entries[key] = ent

        # Botones
        btns = tk.Frame(frm, bg=COLORES["blanco"])
        btns.grid(row=len(campos)*2, column=0, sticky="ew", pady=(16, 0))
        btns.columnconfigure((0, 1), weight=1)

        self.btn_guardar = tk.Button(
            btns, text="💾 Guardar", font=("Segoe UI", 9, "bold"),
            bg=COLORES["acento"], fg="white", relief="flat", cursor="hand2",
            command=self._guardar)
        self.btn_guardar.grid(row=0, column=0, padx=2, sticky="ew", ipady=6)

        tk.Button(
            btns, text="🗑 Limpiar", font=("Segoe UI", 9),
            bg=COLORES["borde"], fg=COLORES["texto"], relief="flat", cursor="hand2",
            command=self._limpiar_form).grid(row=0, column=1, padx=2, sticky="ew", ipady=6)

        tk.Button(
            btns, text="❌ Eliminar", font=("Segoe UI", 9),
            bg=COLORES["peligro"], fg="white", relief="flat", cursor="hand2",
            command=self._eliminar).grid(row=1, column=0, columnspan=2,
                                          sticky="ew", pady=(6, 0), ipady=6)

    def _construir_tabla(self, parent):
        frm = tk.Frame(parent, bg=COLORES["blanco"])
        frm.grid(row=0, column=1, sticky="nsew")
        frm.rowconfigure(1, weight=1)
        frm.columnconfigure(0, weight=1)

        # Barra búsqueda
        barra = tk.Frame(frm, bg=COLORES["blanco"], pady=10, padx=12)
        barra.grid(row=0, column=0, sticky="ew")
        tk.Label(barra, text="🔍", bg=COLORES["blanco"],
                 font=("Segoe UI", 12)).pack(side="left")
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace_add("write", lambda *a: self._cargar_tabla())
        tk.Entry(barra, textvariable=self.var_buscar, font=("Segoe UI", 10),
                 relief="flat", bg=COLORES["fondo"], width=30).pack(
            side="left", ipady=6, padx=6)

        # Treeview
        cols = ("id", "nombre", "codigo", "marca", "precio", "cantidad", "estado")
        self.tv = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")
        headers = {"id": ("ID", 45), "nombre": ("Nombre", 180), "codigo": ("Código", 80),
                   "marca": ("Marca", 90), "precio": ("Precio", 90),
                   "cantidad": ("Stock", 60), "estado": ("Estado", 80)}
        for c, (h, w) in headers.items():
            self.tv.heading(c, text=h)
            self.tv.column(c, width=w, anchor="center" if c not in ("nombre",) else "w")

        # Tags de color
        self.tv.tag_configure("sin_stock",  background="#fdecea")
        self.tv.tag_configure("bajo_stock", background="#fff3e0")
        self.tv.tag_configure("ok",         background="#f0fff4")

        # Scrollbars
        sb_y = ttk.Scrollbar(frm, orient="vertical",   command=self.tv.yview)
        sb_x = ttk.Scrollbar(frm, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tv.grid(row=1, column=0, sticky="nsew")
        sb_y.grid(row=1, column=1, sticky="ns")
        sb_x.grid(row=2, column=0, sticky="ew")

        self.tv.bind("<<TreeviewSelect>>", self._on_seleccion)

    # ──────────────── Datos ────────────────

    def _cargar_tabla(self):
        self.tv.delete(*self.tv.get_children())
        filtro = self.var_buscar.get()
        for p in self.ctrl.listar(filtro):
            if p.cantidad == 0:
                tag, estado = "sin_stock", "Sin Stock"
            elif p.cantidad <= 5:
                tag, estado = "bajo_stock", "Bajo Stock"
            else:
                tag, estado = "ok", "Disponible"
            self.tv.insert("", "end", iid=str(p.id),
                           values=(p.id, p.nombre, p.codigo, p.marca,
                                   formato_moneda(p.precio), p.cantidad, estado),
                           tags=(tag,))

    def _on_seleccion(self, _):
        sel = self.tv.selection()
        if not sel:
            return
        pid = int(sel[0])
        p = self.ctrl.obtener_por_id(pid)
        if not p:
            return
        self._id_seleccionado = pid
        self._set_entry("nombre",   p.nombre)
        self._set_entry("codigo",   p.codigo)
        self._set_entry("marca",    p.marca)
        self._set_entry("precio",   str(p.precio))
        self._set_entry("cantidad", str(p.cantidad))
        self._set_entry("detalles", p.detalles)
        self.btn_guardar.configure(text="✏️ Actualizar")

    # ──────────────── Acciones ────────────────

    def _guardar(self):
        datos = self._leer_form()
        if self._id_seleccionado:
            ok, msg = self.ctrl.editar(self._id_seleccionado, **datos)
        else:
            ok, msg = self.ctrl.agregar(**datos)
        if ok:
            messagebox.showinfo("Éxito", msg)
            self._limpiar_form()
            self._cargar_tabla()
        else:
            messagebox.showerror("Error", msg)

    def _eliminar(self):
        if not self._id_seleccionado:
            messagebox.showwarning("Atención", "Selecciona un producto de la tabla.")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
            ok, msg = self.ctrl.eliminar(self._id_seleccionado)
            if ok:
                messagebox.showinfo("Éxito", msg)
                self._limpiar_form()
                self._cargar_tabla()
            else:
                messagebox.showerror("Error", msg)

    def _limpiar_form(self):
        self._id_seleccionado = None
        self.btn_guardar.configure(text="💾 Guardar")
        for key, ent in self._entries.items():
            if isinstance(ent, tk.Text):
                ent.delete("1.0", "end")
            else:
                ent.delete(0, "end")
        self.tv.selection_remove(self.tv.selection())

    # ──────────────── Helpers ────────────────

    def _leer_form(self) -> dict:
        d = {}
        for key, ent in self._entries.items():
            if isinstance(ent, tk.Text):
                d[key] = ent.get("1.0", "end-1c").strip()
            else:
                d[key] = ent.get().strip()
        return d

    def _set_entry(self, key, value):
        ent = self._entries[key]
        if isinstance(ent, tk.Text):
            ent.delete("1.0", "end")
            ent.insert("1.0", value)
        else:
            ent.delete(0, "end")
            ent.insert(0, value)

