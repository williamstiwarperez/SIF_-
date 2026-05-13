# views/clientes_view.py
# ══════════════════════════════════════════════════════════════════
#  PANTALLA DE REGISTRO DE CLIENTES
#  Tarea: Registro de clientes
#
#  Permite crear, editar, ver y eliminar clientes del sistema.
# ══════════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk, messagebox
import database as db
import auditoria
from utils.helpers import COLORES

# Variable global para saber quién está logueado (se asigna desde ventana_principal)
USUARIO_ACTUAL = {"id": None, "nombre": "sistema"}


class ClientesView(tk.Frame):
    def __init__(self, parent, usuario=None):
        super().__init__(parent, bg=COLORES["fondo"])
        # Guardar datos del usuario logueado para la auditoría
        if usuario:
            USUARIO_ACTUAL["id"] = usuario["id"]
            USUARIO_ACTUAL["nombre"] = usuario["usuario"]
        self._id_sel = None
        self._construir()
        self._cargar()

    # ──────────────── Construcción de la interfaz ────────────────

    def _construir(self):
        # Encabezado
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="👥 Registro de Clientes",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")
        tk.Label(header, text="Gestiona el directorio de clientes del negocio",
                 font=("Segoe UI", 10),
                 bg=COLORES["blanco"], fg=COLORES["texto_claro"]).pack(anchor="w")

        # Cuerpo: formulario izquierda | tabla derecha
        body = tk.Frame(self, bg=COLORES["fondo"])
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._construir_formulario(body)
        self._construir_tabla(body)

    def _construir_formulario(self, parent):
        frm = tk.LabelFrame(parent, text="  Datos del Cliente",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=16, pady=12, width=280)
        frm.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        frm.grid_propagate(False)

        campos = [
            ("Nombre completo *",  "nombre"),
            ("Identificación",     "identificacion"),
            ("Teléfono",           "telefono"),
            ("Correo electrónico", "email"),
            ("Dirección",          "direccion"),
        ]

        self._entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(frm, text=label, font=("Segoe UI", 9),
                     fg=COLORES["texto_claro"], bg=COLORES["blanco"],
                     anchor="w").grid(row=i * 2, column=0, sticky="w", pady=(8, 0))
            ent = tk.Entry(frm, font=("Segoe UI", 10),
                           relief="flat", bg=COLORES["fondo"])
            ent.grid(row=i * 2 + 1, column=0, sticky="ew", ipady=5)
            self._entries[key] = ent

        # Botones
        btns = tk.Frame(frm, bg=COLORES["blanco"])
        btns.grid(row=len(campos) * 2, column=0, sticky="ew", pady=(16, 0))
        btns.columnconfigure((0, 1), weight=1)

        self.btn_guardar = tk.Button(
            btns, text="💾 Guardar", font=("Segoe UI", 9, "bold"),
            bg=COLORES["acento"], fg="white", relief="flat", cursor="hand2",
            command=self._guardar)
        self.btn_guardar.grid(row=0, column=0, padx=2, sticky="ew", ipady=6)

        tk.Button(btns, text="🗑 Limpiar", font=("Segoe UI", 9),
                  bg=COLORES["borde"], fg=COLORES["texto"], relief="flat",
                  cursor="hand2", command=self._limpiar).grid(
            row=0, column=1, padx=2, sticky="ew", ipady=6)

        tk.Button(btns, text="❌ Eliminar", font=("Segoe UI", 9),
                  bg=COLORES["peligro"], fg="white", relief="flat",
                  cursor="hand2", command=self._eliminar).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0), ipady=6)

    def _construir_tabla(self, parent):
        frm = tk.Frame(parent, bg=COLORES["blanco"])
        frm.grid(row=0, column=1, sticky="nsew")
        frm.rowconfigure(1, weight=1)
        frm.columnconfigure(0, weight=1)

        # Barra de búsqueda
        barra = tk.Frame(frm, bg=COLORES["blanco"], pady=10, padx=12)
        barra.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(barra, text="🔍", bg=COLORES["blanco"],
                 font=("Segoe UI", 12)).pack(side="left")
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace_add("write", lambda *a: self._cargar())
        tk.Entry(barra, textvariable=self.var_buscar, font=("Segoe UI", 10),
                 relief="flat", bg=COLORES["fondo"], width=30).pack(
            side="left", ipady=6, padx=6)

        # Tabla
        cols = ("id", "nombre", "identificacion", "telefono", "email", "direccion")
        self.tv = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")

        cabeceras = {
            "id":            ("ID",           50),
            "nombre":        ("Nombre",       180),
            "identificacion":("Identificación", 120),
            "telefono":      ("Teléfono",     100),
            "email":         ("Email",        160),
            "direccion":     ("Dirección",    180),
        }
        for c, (h, w) in cabeceras.items():
            self.tv.heading(c, text=h)
            self.tv.column(c, width=w,
                           anchor="w" if c in ("nombre", "email", "direccion") else "center")

        sb_y = ttk.Scrollbar(frm, orient="vertical", command=self.tv.yview)
        sb_x = ttk.Scrollbar(frm, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tv.grid(row=1, column=0, sticky="nsew")
        sb_y.grid(row=1, column=1, sticky="ns")
        sb_x.grid(row=2, column=0, sticky="ew")

        self.tv.bind("<<TreeviewSelect>>", self._on_sel)

        # Contador
        self.lbl_total = tk.Label(frm, text="", font=("Segoe UI", 9),
                                   bg=COLORES["blanco"], fg=COLORES["texto_claro"])
        self.lbl_total.grid(row=3, column=0, sticky="w", padx=8, pady=4)

    # ──────────────── Cargar datos ────────────────

    def _cargar(self):
        self.tv.delete(*self.tv.get_children())
        filtro = self.var_buscar.get()
        clientes = db.obtener_clientes(filtro)
        for c in clientes:
            self.tv.insert("", "end", iid=str(c["id"]), values=(
                c["id"],
                c["nombre"],
                c["identificacion"] or "—",
                c["telefono"] or "—",
                c["email"] or "—",
                c["direccion"] or "—",
            ))
        total = len(self.tv.get_children())
        self.lbl_total.configure(text=f"{total} cliente(s) encontrado(s)")

    def _on_sel(self, _):
        sel = self.tv.selection()
        if not sel:
            return
        cid = int(sel[0])
        clientes = db.obtener_clientes()
        cliente = next((c for c in clientes if c["id"] == cid), None)
        if not cliente:
            return
        self._id_sel = cid
        self._entries["nombre"].delete(0, "end")
        self._entries["nombre"].insert(0, cliente["nombre"])
        self._entries["identificacion"].delete(0, "end")
        self._entries["identificacion"].insert(0, cliente["identificacion"] or "")
        self._entries["telefono"].delete(0, "end")
        self._entries["telefono"].insert(0, cliente["telefono"] or "")
        self._entries["email"].delete(0, "end")
        self._entries["email"].insert(0, cliente["email"] or "")
        self._entries["direccion"].delete(0, "end")
        self._entries["direccion"].insert(0, cliente["direccion"] or "")
        self.btn_guardar.configure(text="✏️ Actualizar")

    # ──────────────── Validaciones ────────────────

    def _validar(self, nombre, identificacion, telefono, email, direccion):
        """
        Valida todos los campos antes de guardar.
        Devuelve (True, "") si todo está bien, o (False, "mensaje de error") si hay problema.
        """
        import re

        # Nombre: obligatorio, solo letras y espacios, mínimo 3 caracteres
        if not nombre:
            return False, "❌ El nombre es obligatorio."
        if len(nombre) < 3:
            return False, "❌ El nombre debe tener al menos 3 letras."
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
            return False, "❌ El nombre solo puede tener letras y espacios.\nNo se permiten números ni símbolos."

        # Identificación: obligatoria, solo números, entre 6 y 15 dígitos
        if not identificacion:
            return False, "❌ La identificación es obligatoria."
        if not identificacion.isdigit():
            return False, "❌ La identificación solo puede tener números.\nEjemplo: 1234567890"
        if len(identificacion) < 6 or len(identificacion) > 15:
            return False, "❌ La identificación debe tener entre 6 y 15 dígitos."

        # Teléfono: obligatorio, solo números, entre 7 y 15 dígitos
        if not telefono:
            return False, "❌ El teléfono es obligatorio."
        telefono_limpio = telefono.replace(" ", "").replace("-", "").replace("+", "")
        if not telefono_limpio.isdigit():
            return False, "❌ El teléfono solo puede tener números.\nEjemplo: 3001234567"
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            return False, "❌ El teléfono debe tener entre 7 y 15 dígitos."

        # Email: obligatorio, debe tener @ y un punto después
        if not email:
            return False, "❌ El correo electrónico es obligatorio."
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "❌ El correo no es válido.\nDebe tener @ y dominio. Ejemplo: juan@gmail.com"
        if len(email) < 6:
            return False, "❌ El correo es demasiado corto."

        # Dirección: obligatoria, mínimo 5 caracteres
        if not direccion:
            return False, "❌ La dirección es obligatoria."
        if len(direccion) < 5:
            return False, "❌ La dirección debe tener al menos 5 caracteres.\nEjemplo: Calle 10 # 5-20"

        return True, ""

    # ──────────────── Acciones CRUD ────────────────

    def _guardar(self):
        nombre         = self._entries["nombre"].get().strip()
        identificacion = self._entries["identificacion"].get().strip()
        telefono       = self._entries["telefono"].get().strip()
        email          = self._entries["email"].get().strip()
        direccion      = self._entries["direccion"].get().strip()

        # Validar todos los campos antes de guardar
        ok_val, msg_val = self._validar(nombre, identificacion, telefono, email, direccion)
        if not ok_val:
            messagebox.showwarning("Campo inválido", msg_val)
            return

        if self._id_sel:
            # Actualizar cliente existente
            ok, msg = db.actualizar_cliente(
                self._id_sel, nombre, identificacion, telefono, email, direccion
            )
            if ok:
                # AUDITORÍA: registrar que se editó un cliente
                auditoria.registrar(
                    USUARIO_ACTUAL["id"], USUARIO_ACTUAL["nombre"],
                    "EDITAR", "clientes", self._id_sel,
                    f"Editó cliente: {nombre}"
                )
        else:
            # Crear cliente nuevo
            ok, msg = db.crear_cliente(nombre, identificacion, telefono, email, direccion)
            if ok:
                # AUDITORÍA: registrar que se creó un cliente
                auditoria.registrar(
                    USUARIO_ACTUAL["id"], USUARIO_ACTUAL["nombre"],
                    "CREAR", "clientes", None,
                    f"Creó cliente: {nombre}"
                )

        if ok:
            messagebox.showinfo("✅ Éxito", msg)
            self._limpiar()
            self._cargar()
        else:
            messagebox.showerror("❌ Error", msg)

    def _eliminar(self):
        if not self._id_sel:
            messagebox.showwarning("Atención", "Selecciona un cliente de la tabla primero.")
            return
        nombre = self._entries["nombre"].get()
        if messagebox.askyesno("Confirmar eliminación",
                               f"¿Seguro que deseas eliminar al cliente '{nombre}'?\n"
                               "Esta acción no se puede deshacer."):
            ok, msg = db.eliminar_cliente(self._id_sel)
            if ok:
                # AUDITORÍA: registrar que se eliminó un cliente
                auditoria.registrar(
                    USUARIO_ACTUAL["id"], USUARIO_ACTUAL["nombre"],
                    "ELIMINAR", "clientes", self._id_sel,
                    f"Eliminó cliente: {nombre}"
                )
                messagebox.showinfo("✅ Éxito", msg)
                self._limpiar()
                self._cargar()
            else:
                messagebox.showerror("❌ Error", msg)

    def _limpiar(self):
        self._id_sel = None
        self.btn_guardar.configure(text="💾 Guardar")
        for ent in self._entries.values():
            ent.delete(0, "end")
        if self.tv.selection():
            self.tv.selection_remove(self.tv.selection())