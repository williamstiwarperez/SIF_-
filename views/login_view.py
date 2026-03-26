# Pantalla de inicio de sesion
import tkinter as tk
from tkinter import messagebox
import database as db
from utils.helpers import COLORES

class LoginView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Iniciar sesión")
        self.geometry("400x480")
        self.resizable(False, False)
        self.configure(bg=COLORES["primario"])
        self._construir()

    def _construir(self):
        # Panel central
        panel = tk.Frame(self, bg=COLORES["blanco"], padx=40, pady=40)
        panel.place(relx=0.5, rely=0.5, anchor="center", width=340, height=380)

        tk.Label(panel, text="📦", font=("Segoe UI", 36),
                 bg=COLORES["blanco"]).pack()
        tk.Label(panel, text="Inventario y Facturación",
                 font=("Segoe UI", 14, "bold"), bg=COLORES["blanco"],
                 fg=COLORES["texto"]).pack(pady=(0, 20))

        # Usuario
        tk.Label(panel, text="Usuario", font=("Segoe UI", 10),
                 bg=COLORES["blanco"], fg=COLORES["texto_claro"],
                 anchor="w").pack(fill="x")
        self.ent_usuario = tk.Entry(panel, font=("Segoe UI", 11),
                                    relief="flat", bg=COLORES["fondo"])
        self.ent_usuario.pack(fill="x", ipady=8, pady=(2, 12))

        # Contraseña
        tk.Label(panel, text="Contraseña", font=("Segoe UI", 10),
                 bg=COLORES["blanco"], fg=COLORES["texto_claro"],
                 anchor="w").pack(fill="x")
        self.ent_pass = tk.Entry(panel, font=("Segoe UI", 11),
                                  show="•", relief="flat", bg=COLORES["fondo"])
        self.ent_pass.pack(fill="x", ipady=8, pady=(2, 24))

        # Botón
        btn = tk.Button(panel, text="Entrar", font=("Segoe UI", 11, "bold"),
                        bg=COLORES["acento"], fg="white", relief="flat",
                        cursor="hand2", command=self._login)
        btn.pack(fill="x", ipady=8)

        # Hint
        tk.Label(panel, text="Admin por defecto: admin / admin123",
                 font=("Segoe UI", 8), bg=COLORES["blanco"],
                 fg=COLORES["texto_claro"]).pack(pady=(12, 0))

        # Enter activa login
        self.bind("<Return>", lambda e: self._login())
        self.ent_usuario.focus()

    def _login(self):
        usuario = self.ent_usuario.get().strip()
        password = self.ent_pass.get()
        if not usuario or not password:
            messagebox.showwarning("Campos vacíos", "Ingresa usuario y contraseña.")
            return
        row = db.autenticar_usuario(usuario, password)
        if row:
            self.destroy()
            from views.ventana_principal import VentanaPrincipal
            VentanaPrincipal(row).mainloop()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
            self.ent_pass.delete(0, "end")



