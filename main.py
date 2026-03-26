import sys
import os

# Asegura que los módulos locales se encuentren correctamente
sys.path.insert(0, os.path.dirname(__file__))

import database as db
from views.login_view import LoginView

def main():
    # 1. Inicializa la base de datos SQLite
    db.inicializar_db()

    # 2. Muestra la pantalla de login
    LoginView().mainloop()

if __name__ == "__main__":
    main()

# python main.py
# admin
# admin123


