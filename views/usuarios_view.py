# CRUD de usuarios (solo accesible para rol 'admin')
import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from utils.helpers import COLORES

class UsuariosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORES["fondo"])
        self._id_sel = None
        self._construir()
        self._cargar()

    def _construir(self):
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Gestión de Usuarios",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")

        body = tk.Frame(self, bg=COLORES["fondo"])
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Formulario
        frm = tk.LabelFrame(body, text="  Datos del Usuario",
                            font=("Segoe UI", 10, "bold"),
                            bg=COLORES["blanco"], fg=COLORES["texto"],
                            padx=16, pady=12, width=260)
        frm.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        frm.grid_propagate(False)

        campos = [
            ("Usuario *",     "usuario"),
            ("Contraseña",    "password"),
        ]
        self._entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(frm, text=label, font=("Segoe UI", 9),
                     fg=COLORES["texto_claro"], bg=COLORES["blanco"],
                     anchor="w").grid(row=i*2, column=0, sticky="w", pady=(8, 0))
            show = "•" if key == "password" else ""
            ent = tk.Entry(frm, font=("Segoe UI", 10), relief="flat",
                           bg=COLORES["fondo"], show=show)
            ent.grid(row=i*2+1, column=0, sticky="ew", ipady=5)
            self._entries[key] = ent

        tk.Label(frm, text="Rol *", font=("Segoe UI", 9),
                 fg=COLORES["texto_claro"], bg=COLORES["blanco"],
                 anchor="w").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.var_rol = tk.StringVar(value="vendedor")
        rol_frame = tk.Frame(frm, bg=COLORES["blanco"])
        rol_frame.grid(row=5, column=0, sticky="w")
        for val in ("admin", "vendedor"):
            tk.Radiobutton(rol_frame, text=val.capitalize(),
                           variable=self.var_rol, value=val,
                           bg=COLORES["blanco"], font=("Segoe UI", 10)).pack(side="left")

        # Botones
        btns = tk.Frame(frm, bg=COLORES["blanco"])
        btns.grid(row=6, column=0, sticky="ew", pady=(16, 0))
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

        # Tabla
        tbl = tk.Frame(body, bg=COLORES["blanco"])
        tbl.grid(row=0, column=1, sticky="nsew")
        tbl.rowconfigure(0, weight=1)
        tbl.columnconfigure(0, weight=1)

        cols = ("id", "usuario", "rol")
        self.tv = ttk.Treeview(tbl, columns=cols, show="headings", selectmode="browse")
        for c, h, w in [("id","ID",50),("usuario","Usuario",200),("rol","Rol",100)]:
            self.tv.heading(c, text=h)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(tbl, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.tv.bind("<<TreeviewSelect>>", self._on_sel)

    def _cargar(self):
        self.tv.delete(*self.tv.get_children())
        for u in db.obtener_usuarios():
            self.tv.insert("", "end", iid=str(u["id"]),
                           values=(u["id"], u["usuario"], u["rol"]))

    def _on_sel(self, _):
        sel = self.tv.selection()
        if not sel:
            return
        uid = int(sel[0])
        vals = self.tv.item(sel[0], "values")
        self._id_sel = uid
        self._entries["usuario"].delete(0, "end")
        self._entries["usuario"].insert(0, vals[1])
        self._entries["password"].delete(0, "end")
        self.var_rol.set(vals[2])
        self.btn_guardar.configure(text="✏️ Actualizar")

    def _guardar(self):
        usuario  = self._entries["usuario"].get().strip()
        password = self._entries["password"].get()
        rol      = self.var_rol.get()
        if not usuario:
            messagebox.showwarning("Error", "El usuario es obligatorio.")
            return
        if self._id_sel:
            ok, msg = db.actualizar_usuario(self._id_sel, usuario, password, rol)
        else:
            if not password:
                messagebox.showwarning("Error", "Ingresa una contraseña.")
                return
            ok, msg = db.crear_usuario(usuario, password, rol)
        if ok:
            messagebox.showinfo("Éxito", msg)
            self._limpiar()
            self._cargar()
        else:
            messagebox.showerror("Error", msg)

    def _eliminar(self):
        if not self._id_sel:
            messagebox.showwarning("Atención", "Selecciona un usuario.")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este usuario?"):
            ok, msg = db.eliminar_usuario(self._id_sel)
            if ok:
                messagebox.showinfo("Éxito", msg)
                self._limpiar()
                self._cargar()
            else:
                messagebox.showerror("Error", msg)

    def _limpiar(self):
        self._id_sel = None
        self.btn_guardar.configure(text="💾 Guardar")
        for e in self._entries.values():
            e.delete(0, "end")
        self.var_rol.set("vendedor")
        self.tv.selection_remove(self.tv.selection())





