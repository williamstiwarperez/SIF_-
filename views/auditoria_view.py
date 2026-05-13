# views/auditoria_view.py
# ══════════════════════════════════════════════════════════════════
#  PANTALLA DE AUDITORÍA
#  Tarea 2: Auditoría — parte visual
#
#  Muestra una tabla con todo el historial de acciones del sistema.
#  Solo accesible para administradores.
# ══════════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk
import auditoria
from utils.helpers import COLORES


class AuditoriaView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORES["fondo"])
        self._construir()
        self._cargar()

    def _construir(self):
        # Encabezado
        header = tk.Frame(self, bg=COLORES["blanco"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="📋 Historial de Auditoría",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORES["blanco"], fg=COLORES["texto"]).pack(anchor="w")
        tk.Label(header, text="Registro de todas las acciones realizadas en el sistema",
                 font=("Segoe UI", 10),
                 bg=COLORES["blanco"], fg=COLORES["texto_claro"]).pack(anchor="w")

        # Barra de filtros
        barra = tk.Frame(self, bg=COLORES["fondo"], pady=8, padx=16)
        barra.pack(fill="x")

        tk.Label(barra, text="Filtrar por tabla:",
                 font=("Segoe UI", 10), bg=COLORES["fondo"],
                 fg=COLORES["texto"]).pack(side="left")

        self.var_tabla = tk.StringVar(value="Todas")
        opciones = ["Todas", "productos", "clientes", "facturas", "usuarios"]
        self.combo_tabla = ttk.Combobox(barra, textvariable=self.var_tabla,
                                         values=opciones, state="readonly", width=15)
        self.combo_tabla.pack(side="left", padx=8)
        self.combo_tabla.bind("<<ComboboxSelected>>", lambda e: self._cargar())

        tk.Button(barra, text="🔄 Actualizar",
                  font=("Segoe UI", 9), bg=COLORES["acento"], fg="white",
                  relief="flat", cursor="hand2",
                  command=self._cargar).pack(side="left", padx=4, ipady=4, ipadx=6)

        # Tabla
        contenedor = tk.Frame(self, bg=COLORES["blanco"])
        contenedor.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)

        cols = ("id", "fecha", "usuario", "accion", "tabla", "registro_id", "detalle")
        self.tv = ttk.Treeview(contenedor, columns=cols, show="headings", selectmode="browse")

        cabeceras = {
            "id":          ("ID",        50),
            "fecha":       ("Fecha/Hora", 150),
            "usuario":     ("Usuario",   100),
            "accion":      ("Acción",    100),
            "tabla":       ("Módulo",    100),
            "registro_id": ("ID afectado", 90),
            "detalle":     ("Detalle",   300),
        }
        for c, (h, w) in cabeceras.items():
            self.tv.heading(c, text=h)
            self.tv.column(c, width=w, anchor="w" if c == "detalle" else "center")

        # Colores por tipo de acción
        self.tv.tag_configure("CREAR",    background="#e8f5e9")  # verde claro
        self.tv.tag_configure("EDITAR",   background="#fff3e0")  # naranja claro
        self.tv.tag_configure("ELIMINAR", background="#fdecea")  # rojo claro
        self.tv.tag_configure("LOGIN",    background="#e3f2fd")  # azul claro

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tv.yview)
        sb_x = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tv.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        # Contador
        self.lbl_total = tk.Label(self, text="", font=("Segoe UI", 9),
                                   bg=COLORES["fondo"], fg=COLORES["texto_claro"])
        self.lbl_total.pack(pady=(0, 8))

    def _cargar(self):
        self.tv.delete(*self.tv.get_children())
        tabla_sel = self.var_tabla.get()

        if tabla_sel == "Todas":
            registros = auditoria.obtener_historial(limite=300)
        else:
            registros = auditoria.obtener_historial_por_tabla(tabla_sel, limite=300)

        for r in registros:
            tag = r["accion"] if r["accion"] in ("CREAR", "EDITAR", "ELIMINAR", "LOGIN") else ""
            self.tv.insert("", "end", values=(
                r["id"],
                r["fecha"],
                r["usuario_nombre"] or "—",
                r["accion"],
                r["tabla"],
                r["registro_id"] or "—",
                r["detalle"] or "",
            ), tags=(tag,))

        total = len(self.tv.get_children())
        self.lbl_total.configure(text=f"Mostrando {total} registro(s)")