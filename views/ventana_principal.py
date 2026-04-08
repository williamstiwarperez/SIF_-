"""
views/ventana_principal.py
--------------------------
Ventana raíz única (Tk). Contiene el menú lateral y el contenedor
principal donde se intercambian los módulos (Frames).
"""
import tkinter as tk
from tkinter import messagebox
from utils.helpers import COLORES


class VentanaPrincipal(tk.Tk):
    def __init__(self, usuario_row):
        super().__init__()
        self.usuario = usuario_row
        self.title("Sistema de Inventario y Facturación")
        self.geometry("1200x700")
        self.minsize(900, 600)
        self.configure(bg=COLORES["fondo"])
        self._modulo_activo = "dashboard"
        self._frame_actual = None
        self._botones_nav = {}

        self._construir_layout()
        self._construir_sidebar()
        self._ir_a("dashboard")

    def _construir_layout(self):
        self.columnconfigure(0, minsize=200)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self, bg=COLORES["primario"], width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        self.contenido = tk.Frame(self, bg=COLORES["fondo"])
        self.contenido.grid(row=0, column=1, sticky="nsew")
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(0, weight=1)

    def _construir_sidebar(self):
        tk.Label(
            self.sidebar, text="📦", font=("Segoe UI", 28),
            bg=COLORES["primario"], fg="white"
        ).pack(pady=(20, 0))

        tk.Label(
            self.sidebar, text="Inventario\ny Facturación",
            font=("Segoe UI", 11, "bold"),
            bg=COLORES["primario"], fg="white", justify="center"
        ).pack(pady=(4, 10))

        tk.Frame(self.sidebar, height=1, bg=COLORES["secundario"]).pack(fill="x", padx=10)

        nombre = self.usuario["usuario"] if self.usuario else "Invitado"
        rol    = self.usuario["rol"]     if self.usuario else ""
        tk.Label(
            self.sidebar, text=f"👤 {nombre}\n({rol})",
            font=("Segoe UI", 9), bg=COLORES["primario"],
            fg="#aab8c8", justify="center"
        ).pack(pady=8)

        tk.Frame(self.sidebar, height=1, bg=COLORES["secundario"]).pack(fill="x", padx=10, pady=(0, 8))

        items_nav = [
            ("🏠  Dashboard",   "dashboard"),
            ("📦  Inventario",  "inventario"),
            ("🧾  Facturación", "facturacion"),
            ("📊  Reportes",    "reportes"),
            ("👥  Usuarios",    "usuarios"),
        ]

        for texto, clave in items_nav:
            btn = tk.Button(
                self.sidebar, text=texto, anchor="w",
                font=("Segoe UI", 10), padx=16,
                bg=COLORES["primario"], fg="white",
                activebackground=COLORES["acento"], activeforeground="white",
                bd=0, cursor="hand2", relief="flat",
                command=lambda c=clave: self._ir_a(c),
            )
            btn.pack(fill="x", pady=1, ipady=6)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORES["secundario"]))
            btn.bind("<Leave>", lambda e, b=btn, c=clave: self._restaurar_btn(b, c))
            self._botones_nav[clave] = btn

        tk.Frame(self.sidebar, bg=COLORES["primario"]).pack(expand=True, fill="both")
        tk.Frame(self.sidebar, height=1, bg=COLORES["secundario"]).pack(fill="x", padx=10)

        tk.Button(
            self.sidebar, text="🚪  Cerrar sesión", anchor="w",
            font=("Segoe UI", 10), padx=16,
            bg=COLORES["primario"], fg="#e74c3c",
            activebackground="#c0392b", activeforeground="white",
            bd=0, cursor="hand2", relief="flat",
            command=self._cerrar_sesion,
        ).pack(fill="x", pady=(4, 20), ipady=6)

    def _restaurar_btn(self, btn, clave):
        if clave == self._modulo_activo:
            btn.configure(bg=COLORES["acento"])
        else:
            btn.configure(bg=COLORES["primario"])

    def _ir_a(self, modulo: str):
        self._modulo_activo = modulo
        for clave, btn in self._botones_nav.items():
            btn.configure(bg=COLORES["acento"] if clave == modulo else COLORES["primario"])
        if self._frame_actual is not None:
            self._frame_actual.destroy()
        frame = self._crear_modulo(modulo)
        frame.grid(row=0, column=0, sticky="nsew")
        self._frame_actual = frame

    def _crear_modulo(self, modulo: str) -> tk.Frame:
        uid = self.usuario["id"]
        
        if modulo == "dashboard":
            from views.dashboard_view import DashboardView
            return DashboardView(self.contenido, self)

        if modulo == "inventario":
            from views.inventario_view import InventarioView
            from controllers.inventario_controller import InventarioController
            return InventarioView(self.contenido, InventarioController(usuario_id=uid))

        if modulo == "facturacion":
            from views.facturacion_view import FacturacionView
            from controllers.facturacion_controller import FacturacionController
            return FacturacionView(self.contenido, FacturacionController(usuario_id=uid))

        if modulo == "reportes":
            from views.reportes_view import ReportesView
            return ReportesView(self.contenido)

        if modulo == "usuarios":
            if self.usuario["rol"] != "admin":
                messagebox.showwarning("Acceso denegado", "Solo el administrador puede gestionar usuarios.")
                return self._crear_modulo("dashboard")
            from views.usuarios_view import UsuariosView
            return UsuariosView(self.contenido)

        f = tk.Frame(self.contenido, bg=COLORES["fondo"])
        tk.Label(f, text=f"Módulo '{modulo}' no encontrado.", bg=COLORES["fondo"]).pack(pady=40)
        return f

    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            self.destroy()
            from views.login_view import LoginView
            LoginView().mainloop()
            



